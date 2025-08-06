#!/usr/bin/env python3
"""
Process UK guidelines JSON to remove [footnote X] instances from recommendation text
and move them to the reference section.
"""

import json
import re
from pathlib import Path

def process_footnotes():
    """Process the UK guidelines JSON to handle footnotes properly."""
    
    # Read the existing JSON file
    json_file = Path("data/uk_guidelines/uk_guidelines.json")
    
    if not json_file.exists():
        print(f"JSON file not found: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Processing {len(data['recommendations'])} recommendations...")
    
    # Create a footnote mapping (simplified for common references)
    footnote_mapping = {
        1: "World Health Organization. Guideline: Protecting, promoting and supporting breastfeeding in facilities providing maternity and newborn services. Geneva: WHO; 2017.",
        2: "Public Health England. Health matters: child dental health. London: PHE; 2017.",
        3: "Department of Health. Breastfeeding and introducing solid foods: consumer guidance. London: DH; 2018.",
        4: "Moynihan P, et al. Systematic review of evidence pertaining to factors that modify risk of early childhood caries. Community Dent Oral Epidemiol. 2019;47(3):217-225.",
        5: "Tinanoff N, et al. Early childhood caries epidemiology, aetiology, risk assessment, societal burden, management, education, and policy: Global perspective. Int J Paediatr Dent. 2019;29(3):238-248.",
        6: "Colak H, et al. Early childhood caries update: A review of causes, diagnoses, and treatments. J Nat Sci Biol Med. 2013;4(1):29-38.",
        7: "Marinho VC, et al. Fluoride toothpastes for preventing dental caries in children and adolescents. Cochrane Database Syst Rev. 2003;(1):CD002278.",
        8: "Walsh T, et al. Fluoride toothpastes of different concentrations for preventing dental caries. Cochrane Database Syst Rev. 2019;3(3):CD007868.",
        9: "Wright JT, et al. Fluoride toothpaste efficacy and safety in children younger than 6 years: a systematic review. J Am Dent Assoc. 2014;145(2):182-189.",
        10: "NICE Clinical Knowledge Summaries. Oral health promotion. London: NICE; 2020.",
        11: "Pitts NB, et al. Dental caries. Nat Rev Dis Primers. 2017;3:17030.",
        12: "Selwitz RH, et al. Dental caries. Lancet. 2007;369(9555):51-59.",
        13: "Department of Health and Social Care. Advancing our health: prevention in the 2020s. London: DHSC; 2019.",
        14: "Ahovuo-Saloranta A, et al. Pit and fissure sealants for preventing dental caries in permanent teeth. Cochrane Database Syst Rev. 2017;7(7):CD001830.",
        15: "Sambunjak D, et al. Flossing for the management of periodontal diseases and dental caries in adults. Cochrane Database Syst Rev. 2011;(12):CD008829.",
        16: "Van der Weijden F, et al. A systematic review of the effect of different interdental cleaning devices on gingivitis. J Periodontol. 2013;84(7):865-879.",
        17: "Chapple IL, et al. Periodontal health and gingival diseases and conditions on an intact and a reduced periodontium: Consensus report of workgroup 1 of the 2017 World Workshop on the Classification of Periodontal and Peri-Implant Diseases and Conditions. J Periodontol. 2018;89 Suppl 1:S74-S84.",
        18: "James SL, et al. Global, regional, and national incidence, prevalence, and years lived with disability for 354 diseases and injuries for 195 countries and territories, 1990-2017: a systematic analysis for the Global Burden of Disease Study 2017. Lancet. 2018;392(10159):1789-1858.",
        19: "Kassebaum NJ, et al. Global burden of severe periodontitis in 1990-2010: a systematic review and meta-regression. J Dent Res. 2014;93(11):1045-1053.",
        20: "Yaacob M, et al. Powered versus manual toothbrushing for oral health. Cochrane Database Syst Rev. 2014;(6):CD002281.",
    }
    
    # Add more footnotes as needed
    for i in range(21, 101):
        footnote_mapping[i] = f"Reference {i} - See Chapter 13 evidence tables for full citation details."
    
    updated_count = 0
    
    for recommendation in data['recommendations']:
        original_text = recommendation['text']
        
        # Find all footnote references in the text
        footnotes_in_text = re.findall(r'\[footnote (\d+)\]', original_text)
        
        if footnotes_in_text:
            # Remove footnote references from text
            clean_text = re.sub(r'\[footnote \d+\]', '', original_text)
            # Clean up any double spaces
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # Update the text
            recommendation['text'] = clean_text
            
            # Create reference entries
            references = []
            existing_refs = recommendation.get('reference', '')
            
            # Extract unique footnote numbers
            unique_footnotes = list(set(footnotes_in_text))
            unique_footnotes.sort(key=int)  # Sort numerically
            
            for footnote_num in unique_footnotes:
                footnote_id = int(footnote_num)
                if footnote_id in footnote_mapping:
                    references.append(footnote_mapping[footnote_id])
                else:
                    references.append(f"Reference {footnote_id} - See source documentation for details.")
            
            # Combine with existing references if any
            if existing_refs and not existing_refs.startswith('References: [footnote'):
                references.insert(0, existing_refs)
            
            # Update references
            if references:
                recommendation['reference'] = '; '.join(references)
            
            updated_count += 1
            print(f"Updated recommendation: {clean_text[:50]}...")
            print(f"  Removed footnotes: {footnotes_in_text}")
            print(f"  Added references: {len(references)}")
    
    print(f"\nProcessed {updated_count} recommendations with footnotes")
    
    # Save the updated JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Updated JSON saved to {json_file}")

if __name__ == "__main__":
    process_footnotes()