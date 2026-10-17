-- Aptitude assessment seed and compatibility migration.
-- Safe to run after database/schema.sql; does not alter or delete existing responses.
BEGIN;

ALTER TABLE public.aptitude_assessments
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- Question text and options are versioned data; rubric maps an option key to an
-- interest dimension point. This is not a correctness/ability test.
INSERT INTO public.aptitude_questions
  (question_key, version, question_text, options, scoring_rubric, skill_dimension, is_active)
VALUES
('interest-01',1,'{"en":"Which kind of activity do you enjoy most?","hi":"आपको किस तरह की गतिविधि सबसे अधिक पसंद है?","mr":"तुम्हाला कोणती कृती सर्वाधिक आवडते?"}'::jsonb,
 '[{"key":"data","label":{"en":"Finding patterns in data","hi":"डेटा में पैटर्न खोजना","mr":"डेटामधील पॅटर्न शोधणे"}},{"key":"software","label":{"en":"Building apps and solving technical problems","hi":"ऐप बनाना और तकनीकी समस्याएँ हल करना","mr":"अॅप तयार करणे आणि तांत्रिक समस्या सोडवणे"}},{"key":"design","label":{"en":"Creative design and understanding users","hi":"रचनात्मक डिज़ाइन और उपयोगकर्ताओं को समझना","mr":"क्रिएटिव्ह डिझाइन आणि वापरकर्त्यांना समजून घेणे"}},{"key":"business","label":{"en":"Planning, communication and leadership","hi":"योजना, संवाद और नेतृत्व","mr":"नियोजन, संवाद आणि नेतृत्व"}}]'::jsonb,
 '{"data":1,"software":1,"design":1,"business":1}'::jsonb,'general',true),
('interest-02',1,'{"en":"Which problem would you prefer to explore?","hi":"आप किस समस्या को समझना चाहेंगे?","mr":"तुम्हाला कोणती समस्या समजून घ्यायला आवडेल?"}'::jsonb,
 '[{"key":"data","label":{"en":"Why a trend appears in a dataset","hi":"डेटासेट में कोई रुझान क्यों दिखता है","mr":"डेटासेटमध्ये एखादा कल का दिसतो"}},{"key":"software","label":{"en":"How to make an app work reliably","hi":"ऐप को भरोसेमंद तरीके से कैसे चलाएँ","mr":"अॅप विश्वासार्हपणे कसे चालवावे"}},{"key":"ai","label":{"en":"How a machine-learning model makes a prediction","hi":"मशीन-लर्निंग मॉडल भविष्यवाणी कैसे करता है","mr":"मशीन लर्निंग मॉडेल अंदाज कसा लावते"}},{"key":"design","label":{"en":"Why people find an interface confusing","hi":"लोगों को कोई इंटरफ़ेस उलझाऊ क्यों लगता है","mr":"लोकांना इंटरफेस गोंधळात टाकणारा का वाटतो"}}]'::jsonb,
 '{"data":1,"software":1,"ai":1,"design":1}'::jsonb,'general',true),
('interest-03',1,'{"en":"Which output would you most enjoy creating?","hi":"आपको इनमें से क्या बनाना पसंद होगा?","mr":"यापैकी काय तयार करायला आवडेल?"}'::jsonb,
 '[{"key":"data","label":{"en":"A clear chart backed by evidence","hi":"डेटा पर आधारित स्पष्ट चार्ट","mr":"पुराव्यावर आधारित स्पष्ट चार्ट"}},{"key":"software","label":{"en":"A useful working web application","hi":"एक उपयोगी वेब ऐप","mr":"उपयुक्त वेब अॅप"}},{"key":"design","label":{"en":"A prototype that is easy to use","hi":"आसानी से इस्तेमाल होने वाला प्रोटोटाइप","mr":"सहज वापरता येणारा प्रोटोटाइप"}},{"key":"business","label":{"en":"A product plan that solves a customer need","hi":"ग्राहक की जरूरत हल करने वाली उत्पाद योजना","mr":"ग्राहकाची गरज सोडवणारी उत्पादन योजना"}}]'::jsonb,
 '{"data":1,"software":1,"design":1,"business":1}'::jsonb,'general',true),
('interest-04',1,'{"en":"Which skill would you most like to practise?","hi":"आप किस कौशल का अभ्यास करना चाहेंगे?","mr":"तुम्हाला कोणत्या कौशल्याचा सराव करायला आवडेल?"}'::jsonb,
 '[{"key":"data","label":{"en":"Statistics and analytical thinking","hi":"सांख्यिकी और विश्लेषणात्मक सोच","mr":"सांख्यिकी आणि विश्लेषणात्मक विचार"}},{"key":"software","label":{"en":"Programming and debugging","hi":"प्रोग्रामिंग और डिबगिंग","mr":"प्रोग्रामिंग आणि डीबगिंग"}},{"key":"ai","label":{"en":"Experimenting with AI models","hi":"AI मॉडल के साथ प्रयोग","mr":"AI मॉडेल्ससोबत प्रयोग"}},{"key":"design","label":{"en":"User research and visual communication","hi":"उपयोगकर्ता शोध और दृश्य संचार","mr":"वापरकर्ता संशोधन आणि दृश्य संवाद"}}]'::jsonb,
 '{"data":1,"software":1,"ai":1,"design":1}'::jsonb,'general',true),
('interest-05',1,'{"en":"When learning something new, what motivates you?","hi":"कुछ नया सीखते समय आपको क्या प्रेरित करता है?","mr":"नवीन शिकताना तुम्हाला कशामुळे प्रेरणा मिळते?"}'::jsonb,
 '[{"key":"data","label":{"en":"Explaining evidence and patterns","hi":"सबूत और पैटर्न समझाना","mr":"पुरावे आणि पॅटर्न समजावणे"}},{"key":"software","label":{"en":"Making a solution work end to end","hi":"समाधान को शुरू से अंत तक काम करते देखना","mr":"संपूर्ण उपाय कार्यरत करणे"}},{"key":"business","label":{"en":"Organising people and decisions","hi":"लोगों और निर्णयों को व्यवस्थित करना","mr":"लोक आणि निर्णयांचे नियोजन करणे"}},{"key":"design","label":{"en":"Making an experience clearer for people","hi":"लोगों के लिए अनुभव को आसान बनाना","mr":"लोकांसाठी अनुभव अधिक सोपा करणे"}}]'::jsonb,
 '{"data":1,"software":1,"business":1,"design":1}'::jsonb,'general',true),
('interest-06',1,'{"en":"Which topic would you choose for a small project?","hi":"छोटी परियोजना के लिए आप कौन-सा विषय चुनेंगे?","mr":"लहान प्रकल्पासाठी तुम्ही कोणता विषय निवडाल?"}'::jsonb,
 '[{"key":"data","label":{"en":"Explore and visualise a dataset","hi":"डेटासेट का विश्लेषण और दृश्यांकन","mr":"डेटासेटचा अभ्यास आणि दृश्यांकन"}},{"key":"software","label":{"en":"Build a simple website or app","hi":"एक सरल वेबसाइट या ऐप बनाना","mr":"साधी वेबसाइट किंवा अॅप तयार करणे"}},{"key":"ai","label":{"en":"Test an AI tool and review its limits","hi":"AI टूल को परखना और उसकी सीमाएँ देखना","mr":"AI साधन तपासणे आणि त्याच्या मर्यादा पाहणे"}},{"key":"business","label":{"en":"Research a customer problem and pitch a solution","hi":"ग्राहक की समस्या समझकर समाधान प्रस्तुत करना","mr":"ग्राहकाची समस्या समजून उपाय मांडणे"}}]'::jsonb,
 '{"data":1,"software":1,"ai":1,"business":1}'::jsonb,'general',true),
('interest-07',1,'{"en":"What kind of feedback do you like receiving?","hi":"आप किस तरह की प्रतिक्रिया पसंद करते हैं?","mr":"तुम्हाला कोणता अभिप्राय आवडतो?"}'::jsonb,
 '[{"key":"data","label":{"en":"Whether my conclusions match the evidence","hi":"क्या मेरे निष्कर्ष सबूतों से मेल खाते हैं","mr":"माझे निष्कर्ष पुराव्यांशी जुळतात का"}},{"key":"software","label":{"en":"Whether my solution works and is reliable","hi":"क्या मेरा समाधान काम करता है और भरोसेमंद है","mr":"माझा उपाय कार्यरत आणि विश्वासार्ह आहे का"}},{"key":"design","label":{"en":"Whether people can use it comfortably","hi":"क्या लोग इसे आसानी से इस्तेमाल कर सकते हैं","mr":"लोक ते सहज वापरू शकतात का"}},{"key":"business","label":{"en":"Whether it solves the right problem","hi":"क्या यह सही समस्या हल करता है","mr":"तो योग्य समस्या सोडवतो का"}}]'::jsonb,
 '{"data":1,"software":1,"design":1,"business":1}'::jsonb,'general',true),
('interest-08',1,'{"en":"What would you like to learn more about next?","hi":"आप आगे किस बारे में सीखना चाहेंगे?","mr":"पुढे तुम्हाला कशाबद्दल अधिक शिकायला आवडेल?"}'::jsonb,
 '[{"key":"data","label":{"en":"Data analysis and visualisation","hi":"डेटा विश्लेषण और दृश्यांकन","mr":"डेटा विश्लेषण आणि दृश्यांकन"}},{"key":"software","label":{"en":"Web development and APIs","hi":"वेब डेवलपमेंट और APIs","mr":"वेब डेव्हलपमेंट आणि APIs"}},{"key":"ai","label":{"en":"AI and machine learning","hi":"AI और मशीन लर्निंग","mr":"AI आणि मशीन लर्निंग"}},{"key":"design","label":{"en":"UI/UX and product design","hi":"UI/UX और उत्पाद डिज़ाइन","mr":"UI/UX आणि उत्पादन डिझाइन"}}]'::jsonb,
 '{"data":1,"software":1,"ai":1,"design":1}'::jsonb,'general',true)
ON CONFLICT (question_key, version) DO NOTHING;

COMMIT;
