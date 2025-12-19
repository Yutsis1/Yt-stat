from dataclasses import dataclass
from openai import OpenAI

from app.config import get_settings
from app.services.youtube import Comment


@dataclass
class CommentCategory:
    """A category of comments identified by the analyzer."""
    name: str
    description: str
    count: int
    percentage: float
    example_comments: list[str]


@dataclass
class AnalysisResult:
    """Result of comment analysis."""
    total_comments: int
    dominant_category: CommentCategory
    most_liked_category: CommentCategory
    all_categories: list[CommentCategory]
    summary: str


class CommentAnalyzer:
    """Service for analyzing YouTube comments using ChatGPT."""
    
    ANALYSIS_PROMPT = """Analyze the following YouTube video comments and categorize them.

For each comment, I'll provide the text and the number of likes it received.

Your task:
1. Identify 4-6 distinct categories of comments (e.g., "Appreciation/Praise", "Questions", "Criticism", "Jokes/Humor", "Personal Stories", "Requests", etc.)
2. Categorize each comment
3. Determine which category is DOMINANT (most comments)
4. Determine which category is MOST LIKED (highest average likes per comment)

Respond in this exact JSON format:
{{
    "categories": [
        {{
            "name": "Category Name",
            "description": "Brief description of this category",
            "count": 15,
            "total_likes": 230,
            "example_comments": ["Example 1", "Example 2"]
        }}
    ],
    "dominant_category": "Category Name",
    "most_liked_category": "Category Name",
    "summary": "A 2-3 sentence summary of the overall comment sentiment and engagement patterns."
}}

COMMENTS TO ANALYZE:
{comments_text}

Respond with valid JSON only, no additional text."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def _format_comments_for_prompt(self, comments: list[Comment]) -> str:
        """Format comments for the analysis prompt."""
        lines = []
        for i, comment in enumerate(comments, 1):
            # Truncate very long comments
            text = comment.text[:500] + "..." if len(comment.text) > 500 else comment.text
            # Clean up newlines for prompt
            text = text.replace('\n', ' ').strip()
            lines.append(f"{i}. [Likes: {comment.like_count}] {text}")
        return '\n'.join(lines)
    
    def analyze(self, comments: list[Comment]) -> AnalysisResult:
        """Analyze comments using ChatGPT and return structured results."""
        import json
        
        if not comments:
            raise ValueError("No comments to analyze")
        
        # Format comments for the prompt
        comments_text = self._format_comments_for_prompt(comments)
        prompt = self.ANALYSIS_PROMPT.format(comments_text=comments_text)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing social media comments and identifying patterns in user engagement. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            content = content.split('\n', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
        
        data = json.loads(content)
        
        # Build category objects
        categories = []
        dominant_cat = None
        most_liked_cat = None
        
        for cat_data in data['categories']:
            count = cat_data['count']
            category = CommentCategory(
                name=cat_data['name'],
                description=cat_data.get('description', ''),
                count=count,
                percentage=round(count / len(comments) * 100, 1),
                example_comments=cat_data.get('example_comments', [])[:2]
            )
            categories.append(category)
            
            if cat_data['name'] == data['dominant_category']:
                dominant_cat = category
            if cat_data['name'] == data['most_liked_category']:
                most_liked_cat = category
        
        # Fallback if categories not found
        if not dominant_cat:
            dominant_cat = max(categories, key=lambda c: c.count)
        if not most_liked_cat:
            most_liked_cat = categories[0]
        
        return AnalysisResult(
            total_comments=len(comments),
            dominant_category=dominant_cat,
            most_liked_category=most_liked_cat,
            all_categories=categories,
            summary=data.get('summary', 'Analysis completed.')
        )


# Singleton instance
_analyzer: CommentAnalyzer | None = None


def get_analyzer() -> CommentAnalyzer:
    """Get or create analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CommentAnalyzer()
    return _analyzer
