# This file exports all individual sales scrapers

# --- IN Scrapers ---
from .mysmartprice_sales import MySmartPriceSalesScraper
from .amazon_sales import AmazonSalesScraper
from .flipkart_sales import FlipkartSalesScraper

# --- US Scrapers ---
from .amazon_com_sales import AmazonComSalesScraper
from .cnet_sales import CnetSalesScraper
from .bestbuy_sales import BestBuySalesScraper

# --- GB Scrapers ---
from .techradar_sales import TechRadarSalesScraper

# --- JP Scrapers ---
from .ascii_jp_sales import AsciiJPSalesScraper
from .impress_watch_sales import ImpressWatchSalesScraper

# --- CN Scrapers ---
from .ithome_sales import ITHomeSalesScraper
from .kuaikeji_sales import KuaiKeJiSalesScraper


__all__ = [
    # IN
    "MySmartPriceSalesScraper",
    "AmazonSalesScraper",
    "FlipkartSalesScraper",
    # US
    "AmazonComSalesScraper",
    "CnetSalesScraper",
    "BestBuySalesScraper",
    # GB
    "TechRadarSalesScraper",
    # JP
    "AsciiJPSalesScraper",
    "ImpressWatchSalesScraper",
    # CN
    "ITHomeSalesScraper",
    "KuaiKeJiSalesScraper"
]