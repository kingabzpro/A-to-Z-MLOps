import os
import random

from dotenv import load_dotenv
from locust import HttpUser, between, task

load_dotenv()

API_KEY = os.getenv("API_KEY")


class NewsClassifierUser(HttpUser):
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    # Sample news titles for testing
    sample_titles = [
        "Breaking: Major Tech Company Announces Revolutionary AI Breakthrough",
        "Sports: Local Team Wins Championship After Dramatic Final",
        "Politics: New Bill Passes Senate with Bipartisan Support",
        "Business: Stock Market Reaches New All-Time High",
        "Technology: New Smartphone Features Revolutionary Battery Life",
        "Entertainment: Popular TV Show Announces Final Season",
        "Science: Researchers Discover New Species in Amazon Rainforest",
        "Health: New Study Reveals Benefits of Mediterranean Diet",
        "Education: University Introduces New AI-Focused Curriculum",
        "Environment: Global Climate Summit Reaches Historic Agreement",
    ]

    def on_start(self):
        """Set up the API key for authentication"""
        self.headers = {"X-API-Key": API_KEY}  # Replace with your actual API key

    @task(2)
    def get_info(self):
        """Test the /info endpoint"""
        self.client.get("/info", headers=self.headers)

    @task(8)
    def predict_news(self):
        """Test the /predict endpoint with random news titles"""
        title = random.choice(self.sample_titles)
        self.client.post("/predict", json={"title": title}, headers=self.headers)

    @task(3)
    def predict_batch(self):
        """Test the /predict/batch endpoint with multiple random news titles"""
        titles = random.sample(self.sample_titles, k=random.randint(2, 5))
        response = self.client.post("/predict/batch", json={"titles": titles}, headers=self.headers)
        # Log rate limit responses for monitoring
        if response.status_code == 429:
            print(f"Rate limited on batch endpoint: {response.json()}")
