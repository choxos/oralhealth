#!/usr/bin/env python3
"""
Extract UK Guidelines and Cochrane SoF data to clean JSON files
Run this locally to generate static data files
"""

import json
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

# Create data directories
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "uk_guidelines").mkdir(exist_ok=True)
(DATA_DIR / "cochrane_sof").mkdir(exist_ok=True)

def extract_uk_guidelines():
    """Extract UK guidelines to JSON"""
    
    chapters = [
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-1-oral-health-assessment-and-care-planning",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-2-diet-and-oral-health",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-3-fluoride-and-oral-health",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-4-fissure-sealants",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-5-cleaning-between-teeth",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-6-toothbrushing",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-7-denture-care",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-8-saliva-and-dry-mouth",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-9-口腔-cancer-and-mouth-cancer-screening",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-10-safeguarding-children-young-people-and-adults-at-risk",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-11-delivering-oral-health-improvement",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-12-behaviour-change",
        "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-13-oral-health-improvement-for-vulnerable-groups"
    ]
    
    # Fix the URL with encoding issue
    chapters[8] = "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-9-oral-cancer-and-mouth-cancer-screening"
    
    guidelines_data = {
        "country": "United Kingdom",
        "guideline_title": "Delivering better oral health: an evidence-based toolkit for prevention",
        "organization": "Department of Health and Social Care",
        "year": 2021,
        "chapters": []
    }
    
    for i, url in enumerate(chapters, 1):
        print(f"Processing Chapter {i}...")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else f"Chapter {i}"
            
            # Extract recommendations
            recommendations = []
            
            # Look for recommendation sections
            content_div = soup.find('div', class_='govspeak') or soup.find('div', class_='content')
            
            if content_div:
                # Find paragraphs that contain recommendations
                paragraphs = content_div.find_all(['p', 'li', 'div'])
                
                for para in paragraphs:
                    text = para.get_text().strip()
                    
                    # Look for recommendation indicators
                    if any(indicator in text.lower() for indicator in [
                        'recommend', 'should', 'evidence suggests', 'guidance', 
                        'best practice', 'clinical practice', 'prevention'
                    ]):
                        if len(text) > 50:  # Filter out short text
                            
                            # Determine strength (simplified)
                            strength = "Moderate"
                            if "strongly recommend" in text.lower() or "must" in text.lower():
                                strength = "Strong"
                            elif "may" in text.lower() or "consider" in text.lower():
                                strength = "Weak"
                            
                            recommendations.append({
                                "text": text,
                                "strength": strength,
                                "evidence_quality": "Moderate",  # Default
                                "topic": extract_topic_from_title(title),
                                "source_url": url
                            })
            
            chapter_data = {
                "chapter_number": i,
                "title": title,
                "url": url,
                "recommendations": recommendations
            }
            
            guidelines_data["chapters"].append(chapter_data)
            print(f"  Found {len(recommendations)} recommendations")
            
        except Exception as e:
            print(f"Error processing chapter {i}: {e}")
            continue
    
    # Save to JSON
    output_file = DATA_DIR / "uk_guidelines" / "uk_guidelines.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(guidelines_data, f, indent=2, ensure_ascii=False)
    
    print(f"UK Guidelines saved to {output_file}")
    return guidelines_data

def extract_topic_from_title(title):
    """Extract topic from chapter title"""
    title_lower = title.lower()
    
    if "diet" in title_lower:
        return "Diet and Nutrition"
    elif "fluoride" in title_lower:
        return "Fluoride"
    elif "fissure" in title_lower:
        return "Fissure Sealants"
    elif "clean" in title_lower or "interdental" in title_lower:
        return "Interdental Cleaning"
    elif "toothbrush" in title_lower:
        return "Toothbrushing"
    elif "denture" in title_lower:
        return "Denture Care"
    elif "saliva" in title_lower or "dry mouth" in title_lower:
        return "Saliva and Dry Mouth"
    elif "cancer" in title_lower:
        return "Oral Cancer Screening"
    elif "safeguard" in title_lower:
        return "Safeguarding"
    elif "behaviour" in title_lower:
        return "Behaviour Change"
    elif "vulnerable" in title_lower:
        return "Vulnerable Groups"
    elif "assessment" in title_lower:
        return "Assessment and Care Planning"
    elif "improvement" in title_lower:
        return "Oral Health Improvement"
    else:
        return "General"

def extract_cochrane_sof():
    """Extract Cochrane SoF data to JSON"""
    
    cochrane_dir = Path.home() / "Documents/Github/CoE-Cochrane/validated/SoF"
    
    if not cochrane_dir.exists():
        print(f"Cochrane directory not found: {cochrane_dir}")
        return
    
    sof_data = {
        "source": "Cochrane Oral Health Reviews",
        "extracted_date": "2024",
        "reviews": []
    }
    
    # Process all CSV files
    csv_files = list(cochrane_dir.glob("**/*.csv"))
    print(f"Found {len(csv_files)} Cochrane SoF CSV files")
    
    for csv_file in csv_files[:10]:  # Process first 10 for testing
        try:
            print(f"Processing {csv_file.name}...")
            
            df = pd.read_csv(csv_file)
            
            # Extract review info from filename
            review_id = csv_file.stem.split('.')[0]  # e.g., CD000979
            
            # Process SoF entries
            sof_entries = []
            
            for _, row in df.iterrows():
                entry = {
                    "outcome": str(row.get("Outcome", "")),
                    "intervention": str(row.get("Intervention", "")),
                    "comparison": str(row.get("Comparison", "")),
                    "participants": str(row.get("Participants", "")),
                    "studies": str(row.get("Studies", "")),
                    "effect": str(row.get("Effect", "")),
                    "certainty": str(row.get("Certainty", "")),
                    "comments": str(row.get("Comments", ""))
                }
                sof_entries.append(entry)
            
            review_data = {
                "review_id": review_id,
                "filename": csv_file.name,
                "sof_entries": sof_entries
            }
            
            sof_data["reviews"].append(review_data)
            print(f"  Processed {len(sof_entries)} SoF entries")
            
        except Exception as e:
            print(f"Error processing {csv_file.name}: {e}")
            continue
    
    # Save to JSON
    output_file = DATA_DIR / "cochrane_sof" / "cochrane_sof.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sof_data, f, indent=2, ensure_ascii=False)
    
    print(f"Cochrane SoF data saved to {output_file}")
    return sof_data

if __name__ == "__main__":
    print("Extracting UK Guidelines...")
    uk_data = extract_uk_guidelines()
    
    print("\nExtracting Cochrane SoF data...")
    cochrane_data = extract_cochrane_sof()
    
    print(f"\nExtraction complete!")
    print(f"UK Guidelines: {len(uk_data.get('chapters', []))} chapters")
    if cochrane_data:
        print(f"Cochrane SoF: {len(cochrane_data.get('reviews', []))} reviews")