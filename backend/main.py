from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="KisaanAI")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsItem(BaseModel):
    id: int
    title: str
    excerpt: str
    date: str
    source: str
    category: str
    color: str
    image_url: str
    video_url: str | None = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/news", response_model=List[NewsItem])
def get_news():
    return [
        {
            "id": 1,
            "title": "Government Announces MSP Hike for Kharif Crops 2024",
            "excerpt": "The Cabinet Committee on Economic Affairs has approved a significant increase in the Minimum Support Price for paddy and pulses to boost farmer income.",
            "date": "Feb 15, 2026",
            "source": "PIB India",
            "category": "Policy",
            "color": "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
            "image_url": "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?q=80&w=800&auto=format&fit=crop",
            "video_url": None
        },
        {
            "id": 2,
            "title": "Heavy Rainfall Alert: Orange Warning for Maharashtra & Gujarat",
            "excerpt": "IMD forecasts heavy to very heavy rainfall in isolated places. Farmers are advised to ensure proper drainage in fields to prevent waterlogging.",
            "date": "Feb 14, 2026",
            "source": "IMD Weather",
            "category": "Weather Alert",
            "color": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
            "image_url": "https://images.unsplash.com/photo-1514632542131-add7d86241a8?q=80&w=800&auto=format&fit=crop",
            "video_url": "https://cdn.pixabay.com/video/2023/10/12/184734-874249122_large.mp4"
        },
        {
            "id": 3,
            "title": "Onion Prices Surge by 20% in Nasik Mandi",
            "excerpt": "Due to supply chain disruptions, onion prices have seen a sharp rise. Experts predict prices to stabilize within the next two weeks as new stock arrives.",
            "date": "Feb 12, 2026",
            "source": "Mandi News",
            "category": "Market Trend",
            "color": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
            "image_url": "https://images.unsplash.com/photo-1488459716781-31db52582fe9?q=80&w=800&auto=format&fit=crop",
            "video_url": None
        },
        {
            "id": 4,
            "title": "New Subsidy Scheme for Drip Irrigation Systems",
            "excerpt": "State government launches 50% subsidy scheme for adopting micro-irrigation technologies. Applications open from March 1st.",
            "date": "Feb 10, 2026",
            "source": "Agri Dept",
            "category": "Subsidy",
            "color": "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
            "image_url": "https://images.unsplash.com/photo-1560493676-04071c5f467b?q=80&w=800&auto=format&fit=crop",
            "video_url": None
        }
    ]
