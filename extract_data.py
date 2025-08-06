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
    """Extract UK guidelines from Chapter 13 tables only"""
    
    # Only extract from Chapter 13: Evidence base for recommendations
    chapter_13_url = "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-13-evidence-base-for-recommendations-in-the-summary-guidance-tables"
    
    # Chapter URLs for linking back to detailed chapters
    chapter_urls = {
        1: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-1-oral-health-assessment-and-care-planning",
        2: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-2-diet-and-oral-health",
        3: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-3-fluoride-and-oral-health",
        4: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-4-fissure-sealants",
        5: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-5-cleaning-between-teeth",
        6: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-6-toothbrushing",
        7: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-7-denture-care",
        8: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-8-saliva-and-dry-mouth",
        9: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-9-oral-cancer-and-mouth-cancer-screening",
        10: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-10-safeguarding-children-young-people-and-adults-at-risk",
        11: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-11-delivering-oral-health-improvement",
        12: "https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-12-behaviour-change"
    }
    
    guidelines_data = {
        "country": "United Kingdom",
        "guideline_title": "Delivering better oral health: an evidence-based toolkit for prevention",
        "organization": "Department of Health and Social Care",
        "year": 2021,
        "source_url": chapter_13_url,
        "recommendations": []
    }
    
    print("Processing Chapter 13 evidence tables...")
    
    try:
        response = requests.get(chapter_13_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all tables in the content
        content_div = soup.find('div', class_='govspeak') or soup.find('div', class_='content')
        
        if content_div:
            tables = content_div.find_all('table')
            print(f"Found {len(tables)} tables")
            
            for table_idx, table in enumerate(tables):
                # Extract table headers to understand structure
                headers = []
                header_row = table.find('tr')
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                
                print(f"Table {table_idx + 1} headers: {headers}")
                
                # Extract table rows
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row_idx, row in enumerate(rows):
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    
                    # Clean up cell content and remove excess whitespace
                    cells = [' '.join(cell.split()) for cell in cells]
                    
                    if len(cells) >= 2 and cells[0]:  # At least recommendation and strength
                        recommendation_text = cells[0]
                        strength_and_evidence = cells[1] if len(cells) > 1 else ""
                        
                        # Extract strength and evidence from the combined cell
                        strength = extract_strength_from_text(strength_and_evidence)
                        evidence_quality = extract_evidence_quality_from_text(strength_and_evidence)
                        
                        if recommendation_text and len(recommendation_text) > 30:
                            # Determine topic and link to detailed chapter
                            topic, chapter_num = determine_topic_and_chapter(recommendation_text)
                            detailed_chapter_url = chapter_urls.get(chapter_num, "")
                            
                            # Get table context for better categorization
                            table_context = get_table_context(table_idx, headers)
                            
                            recommendation = {
                                "text": recommendation_text,
                                "strength": strength,
                                "evidence_quality": evidence_quality,
                                "topic": topic,
                                "table_context": table_context,
                                "reference": extract_references_from_text(strength_and_evidence),
                                "source_url": chapter_13_url,
                                "detailed_chapter_url": detailed_chapter_url,
                                "chapter_number": chapter_num,
                                "table_index": table_idx + 1,
                                "row_index": row_idx + 1
                            }
                            
                            guidelines_data["recommendations"].append(recommendation)
                            print(f"  Added recommendation: {recommendation_text[:60]}...")
            
            print(f"Extracted {len(guidelines_data['recommendations'])} recommendations from tables")
            
        else:
            print("Could not find main content div")
            
    except Exception as e:
        print(f"Error processing Chapter 13: {e}")
        # Create sample data for testing
        guidelines_data["recommendations"] = [
            {
                "text": "Sample recommendation from Chapter 13 table extraction",
                "strength": "Strong",
                "evidence_quality": "High",
                "topic": "General",
                "reference": "Sample reference",
                "source_url": chapter_13_url,
                "detailed_chapter_url": chapter_urls[1],
                "chapter_number": 1,
                "table_index": 1
            }
        ]
    
    # Save to JSON
    output_file = DATA_DIR / "uk_guidelines" / "uk_guidelines.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(guidelines_data, f, indent=2, ensure_ascii=False)
    
    print(f"UK Guidelines saved to {output_file}")
    return guidelines_data

def determine_topic_and_chapter(recommendation_text):
    """Determine topic and chapter number from recommendation text"""
    text_lower = recommendation_text.lower()
    
    if any(word in text_lower for word in ["diet", "sugar", "food", "nutrition"]):
        return "Diet and Nutrition", 2
    elif any(word in text_lower for word in ["fluoride", "toothpaste", "mouth rinse"]):
        return "Fluoride", 3
    elif any(word in text_lower for word in ["fissure", "sealant"]):
        return "Fissure Sealants", 4
    elif any(word in text_lower for word in ["interdental", "floss", "clean between"]):
        return "Interdental Cleaning", 5
    elif any(word in text_lower for word in ["toothbrush", "brush"]):
        return "Toothbrushing", 6
    elif any(word in text_lower for word in ["denture", "dental prosthes"]):
        return "Denture Care", 7
    elif any(word in text_lower for word in ["saliva", "dry mouth", "xerostomia"]):
        return "Saliva and Dry Mouth", 8
    elif any(word in text_lower for word in ["cancer", "screening", "oral examination"]):
        return "Oral Cancer Screening", 9
    elif any(word in text_lower for word in ["safeguard", "child protection", "vulnerable adult"]):
        return "Safeguarding", 10
    elif any(word in text_lower for word in ["oral health improvement", "population"]):
        return "Oral Health Improvement", 11
    elif any(word in text_lower for word in ["behaviour", "motivation", "counseling"]):
        return "Behaviour Change", 12
    elif any(word in text_lower for word in ["assessment", "care plan", "risk"]):
        return "Assessment and Care Planning", 1
    else:
        return "General", 1

def normalize_strength(strength_text):
    """Normalize strength of recommendation"""
    strength_lower = strength_text.lower().strip()
    
    if any(word in strength_lower for word in ["strong", "grade a", "high"]):
        return "Strong"
    elif any(word in strength_lower for word in ["weak", "conditional", "grade b", "low"]):
        return "Weak"
    elif any(word in strength_lower for word in ["moderate", "grade c"]):
        return "Moderate"
    else:
        return "Moderate"  # Default

def normalize_evidence_quality(evidence_text):
    """Normalize evidence quality"""
    evidence_lower = evidence_text.lower().strip()
    
    if any(word in evidence_lower for word in ["high", "grade a", "systematic review", "rct"]):
        return "High"
    elif any(word in evidence_lower for word in ["low", "grade c", "case series", "expert opinion"]):
        return "Low"
    elif any(word in evidence_lower for word in ["very low", "grade d"]):
        return "Very Low"
    elif any(word in evidence_lower for word in ["moderate", "grade b"]):
        return "Moderate"
    else:
        return "Moderate"  # Default

def extract_strength_from_text(text):
    """Extract strength from combined text"""
    text_lower = text.lower()
    
    if text.startswith("Strong"):
        return "Strong"
    elif text.startswith("Conditional"):
        return "Conditional"
    elif "strong" in text_lower:
        return "Strong"
    elif "conditional" in text_lower or "weak" in text_lower:
        return "Conditional"
    else:
        return "Moderate"

def extract_evidence_quality_from_text(text):
    """Extract evidence quality from combined text"""
    text_lower = text.lower()
    
    if "high certainty" in text_lower or "moderate certainty" in text_lower:
        return "High" if "high" in text_lower else "Moderate"
    elif "low certainty" in text_lower:
        return "Low"
    elif "very low certainty" in text_lower:
        return "Very Low"
    else:
        return "Moderate"

def extract_references_from_text(text):
    """Extract reference information from text"""
    # Look for footnote references
    import re
    footnotes = re.findall(r'\[footnote \d+\]', text)
    if footnotes:
        return f"References: {', '.join(footnotes)}"
    return ""

def get_table_context(table_idx, headers):
    """Get context for the table based on its position and headers"""
    table_contexts = [
        "Dental Caries",
        "Periodontal Diseases", 
        "Oral Cancer",
        "Tooth Wear"
    ]
    
    if table_idx < len(table_contexts):
        return table_contexts[table_idx]
    else:
        return "General"

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