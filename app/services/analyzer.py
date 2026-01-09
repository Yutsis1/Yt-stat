import asyncio
from collections import Counter
import random
from typing import List, Optional
from openai import DefaultAioHttpClient, RateLimitError, AsyncOpenAI
import json
import re

from config import get_settings
from app.modals.video import  Comment, CommentAnalysisResult


class CommentAnalyzer:
    """Service for analyzing YouTube comments using ChatGPT."""

    COMMENT_PROMT_ID = None  # to be loaded from settings
    TOPIC_ANALYSIS_PROMPT_ID = None
    # batch size for processing comments
    BATCH_SIZE = 10
    # max concurrent workers
    MAX_WORKERS = 2

        # IMPORTANT: this is your true concurrency knob now
    MAX_IN_FLIGHT_REQUESTS = 20

    # Retry tuning
    MAX_RETRIES = 6
    BASE_BACKOFF_S = 0.5
    MAX_BACKOFF_S = 20.0

    def __init__(self):
        settings = get_settings()
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            http_client=DefaultAioHttpClient(),
        )
        self.model = settings.openai_model
        # Regex to detect links in comments (http/https or www)
        self.link_regex = re.compile(r"https?://\S+|www\.\S+")
        self.comment_prompt_id = settings.comment_prompt_id
        self.topic_analysis_prompt_id = settings.topic_analysis_prompt_id

    def chunked(self, seq, size):
        """Genreator that yields successive n-sized chunks from seq."""
        for i in range(0, len(seq), size):
            yield i, seq[i:i + size]  # (start_index, batch)

    def contains_link(self, text: str) -> bool:
        """Return True if the given text contains a link."""
        return bool(self.link_regex.search(text))
    
    async def _call_with_retries(self, *, model: str, input, prompt):
        """
        Retry wrapper for transient rate limits.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                return await self.openai_client.responses.create(
                    model=model,
                    input=input,
                    prompt=prompt,
                )
            except RateLimitError as e:
                # If it's quota exhaustion, retries won't help
                if "insufficient_quota" in str(e):
                    raise ValueError(
                        "OpenAI API quota exceeded. Please add credits to your OpenAI account."
                    ) from e

                # Exponential backoff + jitter
                backoff = min(self.MAX_BACKOFF_S, self.BASE_BACKOFF_S * (2**attempt))
                backoff = backoff * (0.75 + 0.5 * random.random())
                await asyncio.sleep(backoff)

        raise RateLimitError("Rate limit: exceeded max retries")

    def _build_prompt(self, prompt_id: str, language: str | None):
        prompt = {"id": prompt_id}
        if language:
            prompt["variables"] = {"language": language}
        return prompt

    async def analyze_single_comment_async(
        self,
        comment: Comment,
        *,
        semaphore: asyncio.Semaphore,
        prompt=None,
        language: str | None = None,
    ) -> Optional[CommentAnalysisResult]:
        if self.contains_link(comment.text):
            return None

        async with semaphore:
            resp = await self._call_with_retries(
                model=self.model,
                input=comment.text,
                prompt=prompt or self._build_prompt(self.comment_prompt_id, language),
            )
            return CommentAnalysisResult(**json.loads(resp.output_text))

    async def categorize_comments_async(
        self,
        comments: List[Comment],
        *,
        language: str | None = None,
    ) -> List[Optional[Comment]]:
        if not comments:
            raise ValueError("No comments to analyze")

        semaphore = asyncio.Semaphore(self.MAX_IN_FLIGHT_REQUESTS)
        results: List[Optional[Comment]] = [None] * len(comments)

        async def worker(i: int, c: Comment):
            c.analysis_result = await self.analyze_single_comment_async(
                c, semaphore=semaphore, language=language
            )
            results[i] = c

        tasks = [asyncio.create_task(worker(i, c)) for i, c in enumerate(comments)]
        await asyncio.gather(*tasks)
        return results

    async def analyze_async(
        self,
        comments: List[Comment],
        *,
        language: str | None = None,
    ) -> str:
        """
        Async version of analyze() that assumes comments already have analysis_result,
        or calls categorize first if you prefer.
        """
        categorized_comments = await self.categorize_comments_async(comments, language=language)
        comments_theme_list = [
            {
                "main_theme": c.analysis_result.main_theme,
                "like_count": c.like_count,
                "sentiment": c.analysis_result.sentiment,
            }
            for c in categorized_comments
            if c and c.analysis_result and c.analysis_result.main_theme
        ]

        resp = await self._call_with_retries(
            model=self.model,
            input=str(comments_theme_list),
            prompt=self._build_prompt(self.topic_analysis_prompt_id, language),
        )
        return resp.output_text

    def categorize_comments(
        self,
        comments: List[Comment],
        *,
        language: str | None = None,
    ) -> List[Optional[Comment]]:
        """Sync wrapper for categorize_comments_async. if needed."""
        return asyncio.run(self.categorize_comments_async(comments, language=language))
    
    @staticmethod
    def count_comment_per_sentiment(comments: List[Comment]) -> Counter:
        """
        Count how often each sentiment category appears in the comments.
        :param comments: Description
        :type comments: List[Comment]
        :return: Description
        :rtype: Counter
        """
        sentiment_counts = Counter(
            f"{comment.analysis_result.sentiment}" for comment in comments if comment.analysis_result
        )
        return sentiment_counts

    @staticmethod
    def count_likes_per_category(comments: List[Comment]) -> Optional[Counter]:
        """
        Determine the sentiment category with the highest total likes.
        :param comments: Description
        :type comments: List[Comment]
        :return: Description
        :rtype: Optional[Sentiment]
        """
        likes_by_sentiment = Counter(
            {s: 0 for s in CommentAnalysisResult.__annotations__['sentiment'].__args__})

        for comment in comments:
            if comment.analysis_result:
                likes_by_sentiment[comment.analysis_result.sentiment] += comment.like_count
        return likes_by_sentiment



# Singleton instance
_analyzer: CommentAnalyzer | None = None


def get_analyzer() -> CommentAnalyzer:
    """Get or create analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CommentAnalyzer()
    return _analyzer
