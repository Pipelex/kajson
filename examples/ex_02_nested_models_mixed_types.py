#!/usr/bin/env python3
"""
Nested Models with Mixed Types Example

This example shows how Kajson handles complex nested Pydantic models
with various types including datetime, timedelta, and lists.
"""

from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel

from kajson import kajson, kajson_manager


class Comment(BaseModel):
    author: str
    text: str
    posted_at: datetime


class BlogPost(BaseModel):
    title: str
    content: str
    published_at: datetime
    read_time: timedelta
    comments: List[Comment]


def main():
    print("=== Nested Models with Mixed Types Example ===\n")

    # Create complex nested structure
    post = BlogPost(
        title="Kajson Makes JSON Easy",
        content="No more 'not JSON serializable' errors!",
        published_at=datetime.now(),
        read_time=timedelta(minutes=5),
        comments=[
            Comment(author="Bob", text="Great post!", posted_at=datetime.now()),
            Comment(author="Carol", text="Very helpful", posted_at=datetime.now()),
        ],
    )

    print(f"Original post: {post}")
    print(f"Post type: {type(post)}")
    print(f"Read time type: {type(post.read_time)}")
    print(f"First comment type: {type(post.comments[0])}")

    # Works seamlessly!
    json_str = kajson.dumps(post)
    print(f"\nSerialized JSON (truncated): {json_str[:200]}...")

    restored = kajson.loads(json_str)
    print(f"\nRestored post: {restored}")
    print(f"Restored type: {type(restored)}")
    print(f"Restored read_time type: {type(restored.read_time)}")
    print(f"Restored first comment type: {type(restored.comments[0])}")

    # Verify reconstruction
    assert post == restored
    print("\n✅ Perfect reconstruction! Original and restored posts are equal.")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
