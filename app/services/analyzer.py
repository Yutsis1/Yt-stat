from collections import Counter
import time
from dataclasses import dataclass
from typing import List, Optional, Literal
from openai import OpenAI, RateLimitError
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import get_settings
from app.modals import ComentAnalysisResult, Comment


class CommentAnalyzer:
    """Service for analyzing YouTube comments using ChatGPT."""

    COMMENT_PROMT_ID = None  # to be loaded from settings
    TOPIC_ANALYSIS_PROMPT_ID = None
    # batch size for processing comments
    BATCH_SIZE = 10
    # max concurrent workers
    MAX_WORKERS = 2

    def __init__(self):
        settings = get_settings()
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        # Regex to detect links in comments (http/https or www)
        self.link_regex = re.compile(r"https?://\S+|www\.\S+")
        self.COMMENT_PROMPT = {
            "id": settings.comment_prompt_id,
            # "variables": {"comment": ""}
            # "version": "1"
        }
        self.TOPIC_ANALYSIS_PROMPT_ID = settings.topic_analysis_prompt_id  

    def chunked(self, seq, size):
        """Genreator that yields successive n-sized chunks from seq."""
        for i in range(0, len(seq), size):
            yield i, seq[i:i + size]  # (start_index, batch)

    def contains_link(self, text: str) -> bool:
        """Return True if the given text contains a link."""
        return bool(self.link_regex.search(text))

    def analyze_single_comment(self, comment: Comment, prompt=None) -> Optional[ComentAnalysisResult]:
        """
        Returns parsed JSON for one comment, or None if skipped.
        """
        if self.contains_link(comment.text):
            return None

        resp = self.openai_client.responses.create(
            model=self.model,
            input=comment.text,
            prompt=prompt or self.COMMENT_PROMPT,
        )
        return ComentAnalysisResult(**json.loads(resp.output_text))

    def process_batch(
            self,
            start_idx: int, 
            batch: List[Comment]
            ) -> List[tuple[int, Optional[Comment]]]:
        """
        Process a batch sequentially; return (absolute_index, result_or_None).
        """
        out = []
        for offset, comment in enumerate(batch):
            idx = start_idx + offset
            try:
                comment.analysis_result = self.analyze_single_comment(comment)
                out.append((idx, comment))
            except Exception as e:
                # out.append((idx, None))
                raise e  # failing for now
        return out

    def analyze_comments_in_batches_in_threads(
            self, comments: List[Comment],
            max_workers: int = None,
            batch_size: int = None
    ) -> List[Optional[Comment]]:
        """
        Runs batches of 10 comments with 2 threads and returns results aligned to input order.
        """
        results = [None] * len(comments)
        max_workers = max_workers or self.MAX_WORKERS
        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:
            futures = []
            batch_size = batch_size or self.BATCH_SIZE
            for start_idx, batch in self.chunked(comments, batch_size):
                futures.append(
                    executor.submit(self.process_batch, start_idx, batch))

            for fut in as_completed(futures):
                batch_results = fut.result()
                for idx, parsed in batch_results:
                    results[idx] = parsed

        # If you want to drop skipped/failed entries entirely:
        # return [r for r in results if r is not None]
        return results

    def categorize_comments(self, comments: List[Comment]) -> List[Optional[Comment]]:
        """Analyze comments using ChatGPT and return structured results."""

        if not comments:
            raise ValueError("No comments to analyze")

        # Call OpenAI API with retry logic for rate limits
        comment_list = []
        try:
            comment_list = self.analyze_comments_in_batches_in_threads(
                comments)

        except RateLimitError as e:
            # Check if it's a quota issue (not retryable) vs temporary rate limit
            if 'insufficient_quota' in str(e):
                raise ValueError(
                    "OpenAI API quota exceeded. Please add credits to your OpenAI account at https://platform.openai.com/account/billing"
                ) from e

        return comment_list
    
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
        likes_by_sentiment = Counter({s: 0 for s in ComentAnalysisResult.__annotations__['sentiment'].__args__})

        for comment in comments:
            if comment.analysis_result:
                likes_by_sentiment[comment.analysis_result.sentiment] += comment.like_count
        return likes_by_sentiment

    
    def analyze(self, comments: List[Comment]) -> str:
        """
        Analyze comments and produce a summary of the analysis.
        :param comments: Description
        :type comments: List[Comment]
        :return: Description
        :rtype: dict
        """
        categorized_comments = self.categorize_comments(comments)
        sentiment_counts = self.count_comment_per_sentiment(comments)
        likes_by_sentiment = self.count_likes_per_category(comments)
        
        comments_theme_list = [
            {
                "main_theme": comment.analysis_result.main_theme, 
                "like_count": comment.like_count, 
                "sentiment": comment.analysis_result.sentiment
            }
            for comment in comments 
            if comment.analysis_result and comment.analysis_result.main_theme
        ]

        resp = self.openai_client.responses.create(
            model=self.model,
            input=comments_theme_list,
            prompt={
                "id": self.TOPIC_ANALYSIS_PROMPT_ID,  
            },
        )
        return resp.output_text
    


# Singleton instance
_analyzer: CommentAnalyzer | None = None


def get_analyzer() -> CommentAnalyzer:
    """Get or create analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CommentAnalyzer()
    return _analyzer
