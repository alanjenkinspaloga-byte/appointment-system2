# ============================================================
# Management Command: seed_symptoms
# ============================================================
# Seeds the database with common medical specializations and
# their associated symptoms/conditions for the search system.
#
# Usage:  python manage.py seed_symptoms
# ============================================================

from django.core.management.base import BaseCommand
from appointments.models import Specialization, Symptom


# --------------------------------------------------
# Seed data: specialization → symptoms mapping
# Includes Pediatrics, Obstetrics & Gynecology, and Dentistry.
# Some symptoms (e.g. headache, fatigue) appear in multiple
# specializations so patients can find the right doctor no
# matter which category they search.
# --------------------------------------------------
SEED_DATA = {
    'Pediatrics': {
        'description': 'Medical care for infants, children, and adolescents — covering general health, development, and childhood diseases.',
        'symptoms': [
            # --- General / Infectious ---
            ('Child Fever', 'Elevated body temperature in an infant or child, often a sign of infection.'),
            ('Child Cough', 'Persistent or recurring cough in a child (dry or wet).'),
            ('Child Cold / Flu', 'Runny nose, sneezing, sore throat, and body aches in a child.'),
            ('Child Sore Throat', 'Throat pain or scratchiness in a child, may indicate pharyngitis or tonsillitis.'),
            ('Child Ear Infection', 'Ear pain, tugging at the ear, irritability — common in young children (otitis media).'),
            ('Child Vomiting', 'Repeated vomiting in a child, may indicate infection or food intolerance.'),
            ('Child Diarrhea', 'Frequent loose or watery stools in a child, risk of dehydration.'),
            ('Child Stomach Pain', 'Abdominal pain or discomfort in a child.'),
            ('Child Constipation', 'Difficulty passing stool or infrequent bowel movements in a child.'),
            ('Child Nausea', 'Feeling of sickness or urge to vomit in a child.'),
            ('Child Dehydration', 'Dry mouth, sunken eyes, less urination in a child — often from diarrhea or vomiting.'),
            # --- Head & Neuro ---
            ('Headache', 'Pain or pressure in the head — can occur in children due to stress, infection, or dehydration.'),
            ('Child Headache', 'Recurring or sudden headache in a child — may be tension, migraine, or illness-related.'),
            ('Child Migraine', 'Throbbing headache with nausea, light sensitivity, or visual aura in a child.'),
            ('Child Dizziness', 'Feeling of light-headedness or unsteadiness in a child.'),
            ('Child Seizure', 'Sudden involuntary movements or convulsions in a child — febrile or epileptic.'),
            ('Febrile Seizure', 'Seizure triggered by high fever in a young child — usually ages 6 months to 5 years.'),
            # --- Skin ---
            ('Childhood Rash', 'Skin rashes or irritation in children (e.g., measles, chickenpox, heat rash).'),
            ('Diaper Rash', 'Red, irritated skin in the diaper area of an infant or toddler.'),
            ('Child Eczema', 'Dry, itchy, inflamed skin patches in a child (atopic dermatitis).'),
            ('Child Hives', 'Raised, itchy red welts on a child\u2019s skin — often from an allergic reaction.'),
            ('Child Insect Bite Reaction', 'Swelling, redness, or allergic response after an insect bite or sting.'),
            ('Child Fungal Infection', 'Ringworm, athlete\u2019s foot, or other fungal skin infections in a child.'),
            ('Impetigo', 'Contagious bacterial skin infection causing red sores and blisters in children.'),
            ('Hand, Foot, and Mouth Disease', 'Sores in the mouth, rash on hands and feet — common in young children.'),
            # --- Respiratory ---
            ('Child Asthma', 'Wheezing, shortness of breath, and coughing episodes in a child.'),
            ('Child Wheezing', 'Whistling sound when the child breathes, often during a cold or asthma.'),
            ('Child Difficulty Breathing', 'Labored or rapid breathing in a child — may be an emergency.'),
            ('Croup', 'Barking cough, hoarse voice, and stridor in a young child.'),
            ('Child Pneumonia', 'Lung infection in a child causing cough, fever, and breathing difficulty.'),
            ('Child Bronchitis', 'Inflammation of the bronchial tubes in a child causing persistent cough.'),
            ('Child Nasal Congestion', 'Stuffy or blocked nose in a child.'),
            ('Child Nosebleed', 'Bleeding from the nose in a child — often from dry air or nose-picking.'),
            ('Child Snoring', 'Loud breathing during sleep in a child — may indicate enlarged tonsils or adenoids.'),
            # --- Eyes & Ears ---
            ('Child Eye Infection', 'Red, itchy, or watery eyes in a child — may be conjunctivitis (pink eye).'),
            ('Pink Eye (Conjunctivitis)', 'Bacterial or viral infection of the eye causing redness and discharge.'),
            ('Child Eye Discharge', 'Pus or crusting around a child\u2019s eye, especially on waking.'),
            ('Child Hearing Problems', 'Difficulty hearing or responding to sounds in a child.'),
            # --- Growth & Development ---
            ('Growth Concerns', 'Concerns about a child\'s height, weight, or physical development milestones.'),
            ('Developmental Delay', 'Late milestones in speech, walking, or cognitive skills in a child.'),
            ('Speech Delay', 'Child not speaking or forming words at the expected age.'),
            ('Poor Weight Gain', 'Failure to thrive — child not gaining weight as expected.'),
            ('Short Stature', 'Child significantly shorter than peers — may need growth evaluation.'),
            ('Delayed Puberty', 'No signs of puberty by expected age in a child.'),
            ('Child Obesity', 'Excessive weight gain in a child relative to age and height.'),
            # --- Behavioral ---
            ('Child Bedwetting', 'Involuntary urination during sleep in a child over age 5 (enuresis).'),
            ('Child Hyperactivity', 'Excessive activity, difficulty focusing, or impulsive behavior in a child.'),
            ('Child Sleep Problems', 'Difficulty falling or staying asleep in a child.'),
            ('Child Anxiety', 'Excessive worrying, nervousness, or fear in a child.'),
            ('Child Tantrums', 'Frequent emotional outbursts beyond what is normal for the child\u2019s age.'),
            ('Child Irritability', 'Unusual fussiness or crankiness in a child that does not resolve.'),
            ('Autism Spectrum Concerns', 'Difficulty with social interaction, communication, or repetitive behaviors.'),
            # --- Immunization & Wellness ---
            ('Vaccination / Immunization', 'Routine vaccinations and immunization schedules for children.'),
            ('Newborn Care', 'General health concerns for newborns — feeding, jaundice, umbilical cord care.'),
            ('Newborn Jaundice', 'Yellowing of the skin and eyes in a newborn due to high bilirubin.'),
            ('Well-Child Checkup', 'Routine health visit to monitor a child\u2019s growth, development, and vaccinations.'),
            # --- Allergies ---
            ('Child Allergies', 'Allergic reactions in children — food, skin, or respiratory allergies.'),
            ('Child Food Allergy', 'Adverse reaction to certain foods in a child (e.g., milk, eggs, nuts).'),
            ('Child Hay Fever', 'Seasonal allergic rhinitis in a child — sneezing, runny nose, itchy eyes.'),
            # --- Infections ---
            ('Chickenpox', 'Itchy blister-like rash all over the body caused by varicella-zoster virus.'),
            ('Measles', 'High fever, cough, runny nose, and widespread rash in a child.'),
            ('Mumps', 'Swollen salivary glands, fever, and headache caused by the mumps virus.'),
            ('Whooping Cough (Pertussis)', 'Severe coughing fits with a "whooping" sound in a child.'),
            ('Child Urinary Tract Infection', 'Painful urination, fever, or foul-smelling urine in a child.'),
            ('Child Tonsillitis', 'Swollen, red tonsils with sore throat and difficulty swallowing in a child.'),
            ('Child Mouth Sores', 'Painful ulcers or sores inside the mouth of a child.'),
            # --- General cross-category ---
            ('Fatigue', 'Persistent tiredness or lack of energy — may be a sign of illness in a child.'),
            ('Loss of Appetite', 'Reduced desire to eat in a child — may indicate illness or emotional distress.'),
            ('Night Sweats', 'Excessive sweating during sleep in a child.'),
            ('Abdominal Bloating', 'Swollen or distended abdomen in a child — may indicate digestive issues.'),
            ('Joint Pain', 'Pain, swelling, or stiffness in a child\u2019s joints.'),
            ('Swollen Lymph Nodes', 'Enlarged glands in the neck, armpits, or groin of a child — often from infection.'),
            ('Child Back Pain', 'Back pain in a child — may be postural, injury-related, or require evaluation.'),
        ],
    },
    'Obstetrics and Gynecology': {
        'description': 'Women\'s reproductive health, pregnancy, prenatal care, childbirth, and gynecological conditions.',
        'symptoms': [
            # --- Menstrual / Gynecological ---
            ('Missed Period', 'Absence of menstrual period when expected — may indicate pregnancy or hormonal issues.'),
            ('Irregular Menstruation', 'Unpredictable, too frequent, or too infrequent menstrual cycles.'),
            ('Heavy Menstrual Bleeding', 'Excessively heavy or prolonged menstrual flow (menorrhagia).'),
            ('Menstrual Cramps', 'Painful cramping during menstruation (dysmenorrhea).'),
            ('Pelvic Pain', 'Pain in the lower abdomen or pelvic region, may be chronic or acute.'),
            ('Vaginal Discharge', 'Unusual color, odor, or amount of discharge from the vagina.'),
            ('Vaginal Itching', 'Itching or irritation in or around the vagina — may indicate infection.'),
            ('Vaginal Bleeding Between Periods', 'Spotting or bleeding outside of the normal menstrual period.'),
            ('Painful Intercourse', 'Pain during or after sexual intercourse (dyspareunia).'),
            ('Vaginal Dryness', 'Insufficient lubrication causing discomfort — common in menopause.'),
            ('Vaginal Odor', 'Unusual or strong odor from the vagina — may indicate bacterial vaginosis.'),
            ('Premenstrual Syndrome (PMS)', 'Mood swings, bloating, breast tenderness, and irritability before a period.'),
            ('Absent Menstruation (Amenorrhea)', 'No menstrual period for 3 or more months outside of pregnancy.'),
            ('Painful Ovulation', 'Sharp pain on one side of the lower abdomen during ovulation (mittelschmerz).'),
            # --- Pregnancy & Prenatal ---
            ('Pregnancy Symptoms', 'Nausea, breast tenderness, fatigue, and missed period suggesting pregnancy.'),
            ('Morning Sickness', 'Nausea and vomiting during early pregnancy.'),
            ('Prenatal Checkup', 'Routine pregnancy monitoring — ultrasound, blood tests, fetal health.'),
            ('Pregnancy Spotting', 'Light bleeding or spotting during pregnancy — may need evaluation.'),
            ('Pregnancy Back Pain', 'Lower back pain during pregnancy due to body changes.'),
            ('Pregnancy Swelling', 'Swelling of feet, ankles, or hands during pregnancy (edema).'),
            ('High Blood Pressure in Pregnancy', 'Elevated blood pressure during pregnancy — risk of preeclampsia.'),
            ('Gestational Diabetes', 'High blood sugar diagnosed during pregnancy.'),
            ('Preterm Contractions', 'Contractions occurring before 37 weeks of pregnancy.'),
            ('Decreased Fetal Movement', 'Reduced or absent baby movements during pregnancy — requires evaluation.'),
            ('Pregnancy Headache', 'Recurring headaches during pregnancy — may be hormonal or a warning sign.'),
            ('Pregnancy Fatigue', 'Extreme tiredness during pregnancy, especially in the first and third trimesters.'),
            ('Pregnancy Heartburn', 'Acid reflux or burning sensation in the chest during pregnancy.'),
            ('Pregnancy Leg Cramps', 'Painful muscle cramps in the legs during pregnancy, often at night.'),
            ('Pregnancy Constipation', 'Difficulty passing stools during pregnancy due to hormonal changes.'),
            ('Pregnancy Nausea', 'Persistent nausea beyond the first trimester of pregnancy.'),
            ('Pregnancy Insomnia', 'Difficulty sleeping during pregnancy due to discomfort or anxiety.'),
            ('Pregnancy Hemorrhoids', 'Swollen veins around the rectum during pregnancy causing pain or bleeding.'),
            ('Pregnancy Varicose Veins', 'Swollen, twisted veins in the legs during pregnancy.'),
            ('Ectopic Pregnancy Symptoms', 'Sharp pelvic pain, vaginal bleeding, dizziness — fertilized egg outside the uterus.'),
            ('Miscarriage Symptoms', 'Heavy bleeding, cramping, and tissue passage during early pregnancy.'),
            ('Postpartum Bleeding', 'Heavy vaginal bleeding after childbirth (lochia) — normal but may need monitoring.'),
            ('Postpartum Depression', 'Feelings of extreme sadness, anxiety, or exhaustion after childbirth.'),
            ('Breastfeeding Problems', 'Difficulty latching, sore nipples, or low milk supply while breastfeeding.'),
            ('Mastitis', 'Breast infection causing redness, swelling, and pain — common during breastfeeding.'),
            # --- Fertility & Reproductive ---
            ('Infertility Concerns', 'Difficulty conceiving after 12 months of regular unprotected intercourse.'),
            ('Polycystic Ovary Syndrome (PCOS)', 'Irregular periods, weight gain, acne, and excess hair growth.'),
            ('Endometriosis', 'Painful periods, pelvic pain, and heavy bleeding — tissue growing outside the uterus.'),
            ('Ovarian Cyst', 'Fluid-filled sac on the ovary causing pelvic pain or bloating.'),
            ('Uterine Fibroids', 'Non-cancerous growths in the uterus causing heavy bleeding and pain.'),
            ('Uterine Prolapse', 'Uterus descends into or protrudes from the vaginal canal — pressure and discomfort.'),
            ('Cervical Polyp', 'Small benign growth on the cervix that may cause bleeding.'),
            ('Pelvic Inflammatory Disease (PID)', 'Infection of the reproductive organs causing pelvic pain and fever.'),
            # --- Menopause ---
            ('Menopause Symptoms', 'Hot flashes, night sweats, mood changes, and irregular periods during menopause.'),
            ('Hot Flashes', 'Sudden feeling of warmth, especially in the face, neck, and chest.'),
            ('Perimenopause Symptoms', 'Irregular periods, mood swings, and sleep disturbances before menopause.'),
            ('Menopause Mood Swings', 'Irritability, anxiety, or depression related to hormonal changes during menopause.'),
            ('Menopause Weight Gain', 'Unexplained weight gain around the midsection during menopause.'),
            # --- Infections ---
            ('Urinary Tract Infection (UTI)', 'Painful or frequent urination, urgency — common in women.'),
            ('Yeast Infection', 'Vaginal itching, thick white discharge, and burning — caused by Candida.'),
            ('Bacterial Vaginosis', 'Thin grayish discharge with fishy odor — bacterial imbalance in the vagina.'),
            ('Sexually Transmitted Infection (STI)', 'Symptoms like sores, discharge, or pain that may indicate an STI.'),
            # --- Screening ---
            ('Pap Smear / Cervical Screening', 'Routine screening for cervical cancer and abnormalities.'),
            ('Breast Lump', 'Lump or mass in the breast — needs evaluation to rule out serious conditions.'),
            ('Breast Pain', 'Pain, tenderness, or soreness in one or both breasts.'),
            ('Breast Discharge', 'Fluid leaking from the nipple outside of pregnancy or breastfeeding.'),
            ('Family Planning / Contraception', 'Consultation about birth control methods and reproductive planning.'),
            ('HPV Vaccine Consultation', 'Questions about HPV vaccination for cervical cancer prevention.'),
            # --- General cross-category ---
            ('Headache', 'Pain or pressure in the head — can be hormonal, tension, or migraine-related.'),
            ('Fatigue', 'Persistent tiredness or lack of energy — may be related to anemia or hormonal changes.'),
            ('Nausea', 'Feeling of sickness or urge to vomit — may be pregnancy-related or hormonal.'),
            ('Dizziness', 'Feeling lightheaded or unsteady — may relate to anemia or blood pressure changes.'),
            ('Bloating', 'Abdominal bloating and fullness — can be hormonal or related to ovarian issues.'),
            ('Lower Back Pain', 'Pain in the lower back — common during menstruation, pregnancy, or pelvic conditions.'),
            ('Night Sweats', 'Excessive sweating during sleep — common in menopause or hormonal changes.'),
            ('Hair Loss', 'Thinning or loss of hair — may be related to hormonal imbalance or PCOS.'),
            ('Acne', 'Breakouts or skin blemishes due to hormonal fluctuations.'),
            ('Mood Swings', 'Rapid changes in mood — may relate to PMS, pregnancy, or menopause.'),
            ('Weight Gain', 'Unexplained weight changes possibly related to hormonal conditions.'),
            ('Anxiety', 'Persistent feelings of worry or nervousness — may be hormone-related.'),
            ('Frequent Urination', 'Needing to urinate often — may indicate UTI, pregnancy, or pelvic pressure.'),
            ('Incontinence', 'Involuntary leakage of urine — stress or urge incontinence in women.'),
        ],
    },
    'Dentistry': {
        'description': 'Dental and oral health care — covering teeth, gums, jaw, and mouth conditions for all ages.',
        'symptoms': [
            # --- Tooth Pain & Sensitivity ---
            ('Toothache', 'Pain in or around a tooth — may indicate decay, infection, or abscess.'),
            ('Tooth Sensitivity', 'Sharp pain when eating or drinking hot, cold, or sweet foods.'),
            ('Tooth Pain When Chewing', 'Pain or discomfort in a tooth when biting down or chewing food.'),
            ('Throbbing Tooth Pain', 'Intense, pulsating pain in a tooth — may indicate infection or abscess.'),
            ('Tooth Abscess', 'Pocket of pus caused by bacterial infection at the root of a tooth.'),
            ('Cracked Tooth', 'Visible crack or fracture in a tooth causing pain or sensitivity.'),
            ('Broken Tooth', 'A chipped or fractured tooth due to trauma or biting hard objects.'),
            ('Loose Tooth (Adult)', 'A permanent tooth that feels loose — may indicate gum disease or injury.'),
            ('Loose Tooth (Child)', 'A baby tooth that is becoming loose — normal part of development.'),
            # --- Gum Problems ---
            ('Bleeding Gums', 'Gums that bleed during brushing or flossing — early sign of gum disease.'),
            ('Swollen Gums', 'Red, puffy, or inflamed gums — may indicate gingivitis or infection.'),
            ('Gum Pain', 'Pain or tenderness in the gums — may be caused by infection or injury.'),
            ('Receding Gums', 'Gum tissue pulling back from the teeth, exposing roots.'),
            ('Gum Abscess', 'Painful swelling in the gum filled with pus — caused by bacterial infection.'),
            ('Gingivitis', 'Mild gum disease with redness, swelling, and bleeding during brushing.'),
            ('Periodontitis', 'Advanced gum disease causing bone loss and potential tooth loss.'),
            # --- Oral / Mouth ---
            ('Mouth Sores', 'Painful ulcers or lesions inside the mouth (canker sores, cold sores).'),
            ('Mouth Ulcer', 'Small painful sore inside the mouth or on the tongue — may recur.'),
            ('Cold Sore', 'Blister on or around the lips caused by herpes simplex virus.'),
            ('Oral Thrush', 'White patches inside the mouth caused by Candida yeast — common in infants.'),
            ('Dry Mouth', 'Insufficient saliva production causing dryness and discomfort.'),
            ('Bad Breath', 'Chronic unpleasant odor from the mouth (halitosis) — may indicate oral health issues.'),
            ('Burning Mouth', 'Burning or tingling sensation in the mouth, tongue, or lips.'),
            ('Mouth Taste Change', 'Metallic, bitter, or unusual taste in the mouth.'),
            ('White Patches in Mouth', 'White spots or patches on the tongue or inner cheeks (leukoplakia).'),
            # --- Tongue ---
            ('Tongue Pain', 'Pain, soreness, or burning on the tongue.'),
            ('Swollen Tongue', 'Enlarged tongue causing discomfort — may be allergic or inflammatory.'),
            ('Geographic Tongue', 'Smooth red patches on the tongue that change location over time.'),
            ('Tongue Discoloration', 'Unusual color on the tongue — white, yellow, or black coating.'),
            # --- Jaw & TMJ ---
            ('Jaw Pain', 'Pain in the jaw area — may be from TMJ disorder, grinding, or infection.'),
            ('Jaw Clicking', 'Clicking or popping sound when opening or closing the mouth.'),
            ('Jaw Locking', 'Jaw gets stuck in open or closed position — TMJ dysfunction.'),
            ('TMJ Disorder', 'Temporomandibular joint pain, stiffness, and clicking.'),
            ('Teeth Grinding (Bruxism)', 'Involuntary grinding or clenching of teeth, often during sleep.'),
            ('Jaw Swelling', 'Swelling in the jaw area — may indicate infection or dental abscess.'),
            # --- Cosmetic & General ---
            ('Tooth Discoloration', 'Yellowing, staining, or dark spots on the teeth.'),
            ('Crooked Teeth', 'Misaligned teeth that may benefit from orthodontic treatment.'),
            ('Missing Tooth', 'Gap from a lost or extracted tooth — may need replacement.'),
            ('Dental Cavity', 'Decay causing a hole in the tooth — needs filling or treatment.'),
            ('Wisdom Tooth Pain', 'Pain, swelling, or infection from erupting or impacted wisdom teeth.'),
            ('Impacted Wisdom Tooth', 'Wisdom tooth stuck beneath the gum causing pain and swelling.'),
            ('Dental Cleaning / Checkup', 'Routine dental cleaning, examination, and preventive care.'),
            ('Dental X-ray Needed', 'Need for dental imaging to diagnose hidden decay, bone loss, or impaction.'),
            ('Tooth Extraction Consultation', 'Consultation about removing a damaged, decayed, or impacted tooth.'),
            ('Denture Problems', 'Ill-fitting dentures causing sores, discomfort, or difficulty eating.'),
            ('Braces / Orthodontic Checkup', 'Routine checkup or adjustment for braces or orthodontic appliances.'),
            ('Teeth Whitening Consultation', 'Consultation about professional teeth whitening options.'),
            # --- Dental Emergencies ---
            ('Knocked-Out Tooth', 'Tooth completely knocked out by trauma — dental emergency.'),
            ('Dental Bleeding', 'Persistent bleeding from the gums or after a dental procedure.'),
            ('Facial Swelling from Tooth', 'Swelling of the face or cheek caused by a dental infection.'),
            ('Post-Extraction Pain', 'Severe pain after tooth removal — may indicate dry socket.'),
            # --- Child Dental ---
            ('Child Toothache', 'Tooth pain in a child — may be decay, eruption, or infection.'),
            ('Child Tooth Decay', 'Cavities or brown spots on a child\u2019s teeth — needs dental treatment.'),
            ('Baby Teething', 'Gum discomfort, drooling, and irritability from erupting baby teeth.'),
            ('Child First Dental Visit', 'Introductory dental checkup recommended around age 1.'),
            ('Child Thumb Sucking', 'Prolonged thumb sucking that may affect dental alignment.'),
            # --- Cross-category ---
            ('Headache', 'Pain or pressure in the head — can be caused by dental issues, TMJ, or teeth grinding.'),
            ('Ear Pain', 'Pain in or around the ear — may be referred pain from a dental problem or TMJ.'),
            ('Sore Throat', 'Throat pain that may be related to oral infection or post-nasal drip.'),
            ('Difficulty Swallowing', 'Trouble swallowing food or liquids — may relate to oral or throat issues.'),
            ('Facial Pain', 'Pain in the face — may stem from dental abscess, sinusitis, or TMJ.'),
            ('Sinus Pressure', 'Pressure or fullness in the sinuses — upper tooth infection can mimic sinusitis.'),
            ('Neck Pain', 'Neck pain or stiffness that may be related to TMJ or dental tension.'),
        ],
    },
}


class Command(BaseCommand):
    help = 'Seed the database with common medical specializations and their symptoms.'

    def handle(self, *args, **options):
        total_specs = 0
        total_symptoms = 0

        for spec_name, data in SEED_DATA.items():
            spec, created = Specialization.objects.get_or_create(
                name=spec_name,
                defaults={'description': data['description']},
            )
            if created:
                total_specs += 1
                self.stdout.write(self.style.SUCCESS(f'  + Specialization: {spec_name}'))
            else:
                self.stdout.write(f'  = Specialization already exists: {spec_name}')

            for symptom_name, symptom_desc in data['symptoms']:
                symptom, sym_created = Symptom.objects.get_or_create(
                    name=symptom_name,
                    defaults={'description': symptom_desc},
                )
                symptom.specializations.add(spec)
                if sym_created:
                    total_symptoms += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {total_specs} specializations and {total_symptoms} symptoms.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Total in DB: {Specialization.objects.count()} specializations, '
            f'{Symptom.objects.count()} symptoms.'
        ))
