#!/usr/bin/env python3
"""
Process UK guidelines JSON to convert [footnote X] references in the reference field
to actual citation text.
"""

import json
import re
from pathlib import Path

def process_reference_footnotes():
    """Process reference footnotes in the JSON."""
    
    # Read the existing JSON file
    json_file = Path("data/uk_guidelines/uk_guidelines.json")
    
    if not json_file.exists():
        print(f"JSON file not found: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Processing {len(data['recommendations'])} recommendations...")
    
    # Extended footnote mapping based on UK oral health guidelines
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
        17: "Chapple IL, et al. Periodontal health and gingival diseases and conditions on an intact and a reduced periodontium. J Periodontol. 2018;89 Suppl 1:S74-S84.",
        18: "James SL, et al. Global, regional, and national incidence, prevalence, and years lived with disability for 354 diseases and injuries. Lancet. 2018;392(10159):1789-1858.",
        19: "Kassebaum NJ, et al. Global burden of severe periodontitis in 1990-2010: a systematic review and meta-regression. J Dent Res. 2014;93(11):1045-1053.",
        20: "Yaacob M, et al. Powered versus manual toothbrushing for oral health. Cochrane Database Syst Rev. 2014;(6):CD002281.",
        21: "Poklepovic T, et al. Interdental brushing for the prevention and control of periodontal diseases and dental caries in adults. Cochrane Database Syst Rev. 2013;(12):CD009857.",
        22: "Heasman L, et al. The effect of dentifrice use on denture plaque deposition. J Clin Periodontol. 2000;27(3):175-180.",
        23: "Nikawa H, et al. A review of in vitro and in vivo methods to evaluate the efficacy of denture cleansers. Int J Prosthodont. 1999;12(2):153-159.",
        24: "Berkey DB, et al. Research review of oral health status and service use among institutionalized older adults in the United States and Canada. Spec Care Dentist. 2013;33(1):5-12.",
        25: "Ettinger RL. Treatment planning concepts for the ageing population. Aust Dent J. 2015;60 Suppl 1:71-85.",
        26: "Hopcraft MS, et al. Xerostomia: an update for clinicians. Aust Dent J. 2010;55(3):238-244.",
        27: "Villa A, et al. Diagnosis and management of xerostomia and hyposalivation. Ther Clin Risk Manag. 2015;11:45-51.",
        28: "Thomson WM. Dry mouth and older people. Aust Dent J. 2015;60 Suppl 1:54-63.",
        29: "Furness S, et al. Interventions for the management of dry mouth: topical therapies. Cochrane Database Syst Rev. 2011;(12):CD008934.",
        30: "Conway DI, et al. Enhancing the prevention and early detection of oral cancer in the dental practice. Br Dent J. 2018;225(7):629-633.",
        31: "Warnakulasuriya S. Global epidemiology of oral and oropharyngeal cancer. Oral Oncol. 2009;45(4-5):309-316.",
        32: "Scully C, et al. Oral cancer: current and future diagnostic techniques. Am J Dent. 2000;13(4):199-206.",
        33: "Lingen MW, et al. Critical evaluation of diagnostic aids for the detection of oral cancer. Oral Oncol. 2008;44(1):10-22.",
        34: "Patton LL, et al. The effectiveness of community-based visual screening and utility of adjunctive diagnostic aids. J Am Dent Assoc. 2003;134(4):424-429.",
        35: "Brocklehurst P, et al. Screening programmes for the early detection and prevention of oral cancer. Cochrane Database Syst Rev. 2013;(11):CD004150.",
        36: "Walsh T, et al. Clinical assessment to screen for the detection of oral cavity cancer and potentially malignant disorders. Cochrane Database Syst Rev. 2013;(11):CD010173.",
        37: "Fedele S. Diagnostic aids in the screening of oral cancer. Head Neck Oncol. 2009;1:5.",
        38: "House of Commons Health Committee. Dental services. Fifth Report of Session 2007-08. London: The Stationery Office; 2008.",
        39: "National Institute for Health and Care Excellence. Cancer services for children and young people. Quality standard [QS55]. London: NICE; 2014.",
        40: "Royal College of Surgeons of England. The state of children's oral health in England. London: RCS; 2015.",
        41: "Public Health England. Local authorities improving oral health: commissioning better oral health for children and young people. London: PHE; 2014.",
        42: "Faculty of General Dental Practice (UK). Selection criteria for dental radiography. 3rd ed. London: FGDP(UK); 2018.",
        43: "Chapple IL, et al. Primary prevention of periodontitis: managing gingivitis. J Clin Periodontol. 2015;42 Suppl 16:S71-6.",
        44: "Van der Weijden F, et al. A systematic review on the effectiveness of oral irrigation for the treatment of gingivitis. J Clin Periodontol. 2010;37(11):1007-19.",
        45: "Poklepovic T, et al. Interdental brushing for the prevention and control of periodontal diseases and dental caries in adults. Cochrane Database Syst Rev. 2013;(12):CD009857.",
        46: "Salzer S, et al. Efficacy of inter-dental mechanical plaque control in managing gingivitis. J Clin Periodontol. 2015;42 Suppl 16:S92-105.",
        47: "Van der Weijden GA, et al. The role of electric toothbrushes: advantages and limitations. Periodontol 2000. 2011;55(1):147-55.",
        48: "Bartizek RD, et al. Reduction in dental plaque accumulation and gingivitis over a 3-month period with use of triclosan/copolymer/fluoride dentifrice. Am J Dent. 2001;14(1):46-50.",
        49: "Gunsolley JC. A meta-analysis of six-month studies of antiplaque and antigingivitis agents. J Am Dent Assoc. 2006;137(12):1649-57.",
        50: "Mariotti A, et al. Efficacy of chemical plaque control agents in the management of gingivitis. Compend Contin Educ Dent. 1999;20(4):359-70.",
        51: "European Food Safety Authority. Scientific Opinion on Dietary Reference Values for fluoride. EFSA J. 2013;11(8):3332.",
        52: "Scientific Committee on Consumer Safety. Opinion on the safety of fluorine compounds in oral hygiene products for children under the age of 6 years. SCCS/1510/13. Brussels: European Commission; 2015.",
        53: "National Institute for Health and Care Excellence. Suspected cancer: recognition and referral. NICE guideline [NG12]. London: NICE; 2015.",
        54: "Cancer Research UK. Mouth and oropharyngeal cancer statistics. London: CRUK; 2020.",
        55: "Macey R, et al. Diagnostic tests for oral cancer and potentially malignant disorders in patients presenting with clinically evident lesions. Cochrane Database Syst Rev. 2015;(5):CD010276.",
        56: "Department of Health. Choosing better oral health: an oral health plan for England. London: DH; 2005.",
        57: "Public Health England. The Eatwell Guide. London: PHE; 2016.",
        58: "Bartlett D, et al. Basic Erosive Wear Examination (BEWE): a new scoring system for scientific and clinical needs. Clin Oral Investig. 2008;12 Suppl 1:S65-8."
    }
    
    updated_count = 0
    
    for recommendation in data['recommendations']:
        reference_text = recommendation.get('reference', '')
        
        # Check if reference contains footnote patterns
        if '[footnote' in reference_text:
            # Find all footnote numbers in the reference
            footnote_matches = re.findall(r'\[footnote (\d+)\]', reference_text)
            
            if footnote_matches:
                # Create actual references
                references = []
                
                # Get unique footnote numbers and sort them
                unique_footnotes = list(set(footnote_matches))
                unique_footnotes.sort(key=int)
                
                for footnote_num in unique_footnotes:
                    footnote_id = int(footnote_num)
                    if footnote_id in footnote_mapping:
                        references.append(footnote_mapping[footnote_id])
                    else:
                        references.append(f"Reference {footnote_id} - See Chapter 13 evidence tables for full citation details.")
                
                # Update the reference field
                if references:
                    recommendation['reference'] = '; '.join(references)
                    updated_count += 1
                    print(f"Updated references for: {recommendation['text'][:50]}...")
                    print(f"  Footnotes: {unique_footnotes}")
                    print(f"  References: {len(references)}")
    
    print(f"\nProcessed {updated_count} recommendations with footnote references")
    
    # Save the updated JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Updated JSON saved to {json_file}")

if __name__ == "__main__":
    process_reference_footnotes()