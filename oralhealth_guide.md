I want to create a database of oral health recommendations based on the latest guidelines, starting from the UK's Delivering better oral health: an evidence-based toolkit for prevention but then gradually covering US, Canada, Australia and New Zealand and other countries. 

I want to create a web app named OralHealth. This is a part of Xera DB. Xera DB projects use a same theme and a same structure. You can find the specifics of the theme and the structure in this folder: ~/Documents/Github/xeradb/shared_theme. The specifics for OralHealth have not been developed previously but put them in css/themes/oralhealth-theme.css. You can find the structure of other projects in ~/Documents/Github/OpenScienceTracker for OST project, ~/Documents/GitHub/CitingRetracted for PRCT project, ~/Documents/GitHub/TTEdb for TTEdb project, and ~/Documents/GitHub/CIHRPT for CIHRPT project. Read each one carefully to understand the structure.

I want you to go through the Delivering better oral health: an evidence-based toolkit for prevention chapters and save it first in a directory:

1. Chapter 1: Introduction: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-1-introduction

2. Chapter 2: Summary guidance tables for dental teams: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-2-summary-guidance-tables-for-dental-teams

3. Chapter 3: Behaviour change: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-3-behaviour-change

4.  Chapter 4: Dental caries: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-4-dental-caries

5. Chapter 5: Periodontal diseases: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-5-periodontal-diseases

6. Chapter 6: Oral cancer: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-6-oral-cancer

7. Chapter 7: Tooth wear: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-7-tooth-wear

8. Chapter 8: Oral hygiene: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-8-oral-hygiene

9. Chapter 9: Fluoride: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-9-fluoride

10. Chapter 10: Healthier eating: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-10-healthier-eating

11. Chapter 11: Smoking and tobacco use: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-11-smoking-and-tobacco-use

12. Chapter 12: Alcohol: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-12-alcohol

13. Chapter 13: Evidence base for recommendations in the summary guidance tables: https://www.gov.uk/government/publications/delivering-better-oral-health-an-evidence-based-toolkit-for-prevention/chapter-13-evidence-base-for-recommendations-in-the-summary-guidance-tables


Then, create a database that includes the recommendation and Strength of recommendation and reference for that decision (in terms of strength of recommendation). So, when a user searches in the search part, they can see each recommendation and their strength of recommendation and then in the recommendation page, they can see the reference for that recommendation with the link to the reference and also which country in which guideline it is from. Also, the link to that recommendation in the guideline should be provided. You can brainstorm about other useful features for recommendations.

In the next step, go through all Cochrane Oral Health reviews and extract their summary of findings tables (SoF, if available) and put it in another page dedicated to Cochrane Oral Health evidence. You can find HTMLs of SoF of Cochrane Oral Health reviews in this folder: ~/Documents/Github/CoE-Cochrane/validated/SoF. Please note that in that folderyou can find extracted and validated CSV files which are much easier to read for you

Then, give me a .md file to deploy the project to my VPS (oralhealth.xeradb.com). The folder is in /var/www/oralhealth and postgres database is oralhealth_production with user name oralhealth_user with pass Choxos10203040.

Let's GO!