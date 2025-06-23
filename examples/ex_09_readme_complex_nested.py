#!/usr/bin/env python3
"""
README Complex Nested Models Example

This example shows how Kajson handles complex nested Pydantic models
with multiple levels of nesting and various field types.
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel

import kajson
from kajson import kajson_manager


class Comment(BaseModel):
    author: str
    content: str
    created_at: datetime


class BlogPost(BaseModel):
    title: str
    content: str
    published_at: datetime
    comments: List[Comment]
    metadata: Dict[str, Any]


def main():
    print("=== README Complex Nested Models Example ===\n")

    # Create complex nested structure
    post = BlogPost(
        title="Introducing Kajson",
        content="A powerful JSON library...",
        published_at=datetime.now(),
        comments=[
            Comment(author="Alice", content="Great post!", created_at=datetime.now()),
            Comment(author="Bob", content="Very helpful", created_at=datetime.now()),
        ],
        metadata={"views": 1000, "likes": 50},
    )

    print(f"Original post: {post}")
    print(f"Post type: {type(post)}")
    print(f"Number of comments: {len(post.comments)}")
    print(f"First comment type: {type(post.comments[0])}")

    # Serialize and deserialize - it just works!
    json_str = kajson.dumps(post)
    print(f"\nSerialized JSON (first 300 chars): {json_str[:300]}...")

    restored_post = kajson.loads(json_str)
    print(f"\nRestored post title: {restored_post.title}")
    print(f"Restored post type: {type(restored_post)}")
    print(f"Restored comments count: {len(restored_post.comments)}")

    # All nested objects are perfectly preserved
    assert isinstance(restored_post.comments[0], Comment)
    assert restored_post.comments[0].created_at.year == datetime.now().year
    print("✅ All nested objects are perfectly preserved!")
    print(f"✅ First comment: {restored_post.comments[0].author} - {restored_post.comments[0].content}")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
