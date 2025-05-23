"""
This is where we submit prompts to OpenAI ChatGPT and retrieve responses to be displayed. Before doing so, make sure
you have both the signed up for an OpenAI account and also obtained a valid API key that is specified in the config.json
file. After which, go crazy and amend the prompts below to your needs. Get ChatGPT to generate a new Haiku every hour,
or tell you a joke. Knock yourself out!
"""

import logging
import random
import openai
from openai import OpenAI
from datetime import datetime


class OAIModule:
    def __init__(self):
        self.logger = logging.getLogger("maginkdash")

    def get_random_fact(self, curr_date, openai_api_key):
        curr_mth_str = curr_date.strftime("%B")
        curr_day_str = curr_date.strftime("%d")

        # Generate random fact from OpenAI
        topics = [
            {
                "title": "Did You Know?",
                "prompt": "Tell me a fun fact in 60 words or less.",
            },
            {
                "title": "All About Animals",
                "prompt": "Tell me an interesting fact about an animal in {} in 60 words or less.".format(
                    self.get_country()[1]
                ),
            },
            {
                "title": "All About Countries",
                "prompt": "Tell me an interesting fact about the country {} in 60 words or less.".format(
                    self.get_country()[1]
                ),
            },
            {
                "title": "Famous People",
                "prompt": "Tell me about a famous historical figure from {} in 60 words or less.".format(
                    self.get_country()[1]
                ),
            },
            {
                "title": "Notable Events",
                "prompt": "Tell me about a notable historical event that happened in {} in 60 words or less.".format(
                    self.get_country()[1]
                ),
            },
            {
                "title": "Notable World Records",
                "prompt": "Tell me about a notable world record in 60 words or less.",
            },
            {
                "title": "Today in History",
                "prompt": "Tell me about a significant historical event that happened on {} {} in 60 words or less.".format(
                    curr_mth_str, curr_day_str
                ),
            },
        ]
        topic = random.choice(topics)

        # Create a client instance with the API key
        client = OpenAI(api_key=openai_api_key)

        # Use the chat completions API instead of the completions API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a current model
            messages=[{"role": "user", "content": topic["prompt"]}],
            temperature=0.75,
            max_tokens=64,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Extract the text from the response (structure is different from old API)
        text = response.choices[0].message.content

        # Process the text to ensure it ends with a period
        last_period = text.rfind(".")
        if last_period == -1:
            topic["text"] = text
        else:
            topic["text"] = text[0 : last_period + 1]

        self.logger.info(topic["title"])
        self.logger.info(topic["text"])

        return topic

    def get_country(self):
        countries = [
            ("US", "United States"),
            ("AF", "Afghanistan"),
            ("AL", "Albania"),
            ("DZ", "Algeria"),
            ("AS", "American Samoa"),
            ("AD", "Andorra"),
            ("AO", "Angola"),
            ("AI", "Anguilla"),
            ("AQ", "Antarctica"),
            ("AG", "Antigua And Barbuda"),
            ("AR", "Argentina"),
            ("AM", "Armenia"),
            ("AW", "Aruba"),
            ("AU", "Australia"),
            ("AT", "Austria"),
            ("AZ", "Azerbaijan"),
            ("BS", "Bahamas"),
            ("BH", "Bahrain"),
            ("BD", "Bangladesh"),
            ("BB", "Barbados"),
            ("BY", "Belarus"),
            ("BE", "Belgium"),
            ("BZ", "Belize"),
            ("BJ", "Benin"),
            ("BM", "Bermuda"),
            ("BT", "Bhutan"),
            ("BO", "Bolivia"),
            ("BA", "Bosnia And Herzegowina"),
            ("BW", "Botswana"),
            ("BV", "Bouvet Island"),
            ("BR", "Brazil"),
            ("BN", "Brunei Darussalam"),
            ("BG", "Bulgaria"),
            ("BF", "Burkina Faso"),
            ("BI", "Burundi"),
            ("KH", "Cambodia"),
            ("CM", "Cameroon"),
            ("CA", "Canada"),
            ("CV", "Cape Verde"),
            ("KY", "Cayman Islands"),
            ("CF", "Central African Rep"),
            ("TD", "Chad"),
            ("CL", "Chile"),
            ("CN", "China"),
            ("CX", "Christmas Island"),
            ("CC", "Cocos Islands"),
            ("CO", "Colombia"),
            ("KM", "Comoros"),
            ("CG", "Congo"),
            ("CK", "Cook Islands"),
            ("CR", "Costa Rica"),
            ("CI", "Cote D`ivoire"),
            ("HR", "Croatia"),
            ("CU", "Cuba"),
            ("CY", "Cyprus"),
            ("CZ", "Czech Republic"),
            ("DK", "Denmark"),
            ("DJ", "Djibouti"),
            ("DM", "Dominica"),
            ("DO", "Dominican Republic"),
            ("TP", "East Timor"),
            ("EC", "Ecuador"),
            ("EG", "Egypt"),
            ("SV", "El Salvador"),
            ("GQ", "Equatorial Guinea"),
            ("ER", "Eritrea"),
            ("EE", "Estonia"),
            ("ET", "Ethiopia"),
            ("FK", "Falkland Islands (Malvinas)"),
            ("FO", "Faroe Islands"),
            ("FJ", "Fiji"),
            ("FI", "Finland"),
            ("FR", "France"),
            ("GF", "French Guiana"),
            ("PF", "French Polynesia"),
            ("TF", "French S. Territories"),
            ("GA", "Gabon"),
            ("GM", "Gambia"),
            ("GE", "Georgia"),
            ("DE", "Germany"),
            ("GH", "Ghana"),
            ("GI", "Gibraltar"),
            ("GR", "Greece"),
            ("GL", "Greenland"),
            ("GD", "Grenada"),
            ("GP", "Guadeloupe"),
            ("GU", "Guam"),
            ("GT", "Guatemala"),
            ("GN", "Guinea"),
            ("GW", "Guinea-bissau"),
            ("GY", "Guyana"),
            ("HT", "Haiti"),
            ("HN", "Honduras"),
            ("HK", "Hong Kong"),
            ("HU", "Hungary"),
            ("IS", "Iceland"),
            ("IN", "India"),
            ("ID", "Indonesia"),
            ("IR", "Iran"),
            ("IQ", "Iraq"),
            ("IE", "Ireland"),
            ("IL", "Israel"),
            ("IT", "Italy"),
            ("JM", "Jamaica"),
            ("JP", "Japan"),
            ("JO", "Jordan"),
            ("KZ", "Kazakhstan"),
            ("KE", "Kenya"),
            ("KI", "Kiribati"),
            ("KP", "Korea (North)"),
            ("KR", "Korea (South)"),
            ("KW", "Kuwait"),
            ("KG", "Kyrgyzstan"),
            ("LA", "Laos"),
            ("LV", "Latvia"),
            ("LB", "Lebanon"),
            ("LS", "Lesotho"),
            ("LR", "Liberia"),
            ("LY", "Libya"),
            ("LI", "Liechtenstein"),
            ("LT", "Lithuania"),
            ("LU", "Luxembourg"),
            ("MO", "Macau"),
            ("MK", "Macedonia"),
            ("MG", "Madagascar"),
            ("MW", "Malawi"),
            ("MY", "Malaysia"),
            ("MV", "Maldives"),
            ("ML", "Mali"),
            ("MT", "Malta"),
            ("MH", "Marshall Islands"),
            ("MQ", "Martinique"),
            ("MR", "Mauritania"),
            ("MU", "Mauritius"),
            ("YT", "Mayotte"),
            ("MX", "Mexico"),
            ("FM", "Micronesia"),
            ("MD", "Moldova"),
            ("MC", "Monaco"),
            ("MN", "Mongolia"),
            ("MS", "Montserrat"),
            ("MA", "Morocco"),
            ("MZ", "Mozambique"),
            ("MM", "Myanmar"),
            ("NA", "Namibia"),
            ("NR", "Nauru"),
            ("NP", "Nepal"),
            ("NL", "Netherlands"),
            ("AN", "Netherlands Antilles"),
            ("NC", "New Caledonia"),
            ("NZ", "New Zealand"),
            ("NI", "Nicaragua"),
            ("NE", "Niger"),
            ("NG", "Nigeria"),
            ("NU", "Niue"),
            ("NF", "Norfolk Island"),
            ("MP", "Northern Mariana Islands"),
            ("NO", "Norway"),
            ("OM", "Oman"),
            ("PK", "Pakistan"),
            ("PW", "Palau"),
            ("PA", "Panama"),
            ("PG", "Papua New Guinea"),
            ("PY", "Paraguay"),
            ("PE", "Peru"),
            ("PH", "Philippines"),
            ("PN", "Pitcairn"),
            ("PL", "Poland"),
            ("PT", "Portugal"),
            ("PR", "Puerto Rico"),
            ("QA", "Qatar"),
            ("RE", "Reunion"),
            ("RO", "Romania"),
            ("RU", "Russian Federation"),
            ("RW", "Rwanda"),
            ("KN", "Saint Kitts And Nevis"),
            ("LC", "Saint Lucia"),
            ("VC", "St Vincent/Grenadines"),
            ("WS", "Samoa"),
            ("SM", "San Marino"),
            ("ST", "Sao Tome"),
            ("SA", "Saudi Arabia"),
            ("SN", "Senegal"),
            ("SC", "Seychelles"),
            ("SL", "Sierra Leone"),
            ("SG", "Singapore"),
            ("SK", "Slovakia"),
            ("SI", "Slovenia"),
            ("SB", "Solomon Islands"),
            ("SO", "Somalia"),
            ("ZA", "South Africa"),
            ("ES", "Spain"),
            ("LK", "Sri Lanka"),
            ("SH", "St. Helena"),
            ("PM", "St.Pierre"),
            ("SD", "Sudan"),
            ("SR", "Suriname"),
            ("SZ", "Swaziland"),
            ("SE", "Sweden"),
            ("CH", "Switzerland"),
            ("SY", "Syrian Arab Republic"),
            ("TW", "Taiwan"),
            ("TJ", "Tajikistan"),
            ("TZ", "Tanzania"),
            ("TH", "Thailand"),
            ("TG", "Togo"),
            ("TK", "Tokelau"),
            ("TO", "Tonga"),
            ("TT", "Trinidad And Tobago"),
            ("TN", "Tunisia"),
            ("TR", "Turkey"),
            ("TM", "Turkmenistan"),
            ("TV", "Tuvalu"),
            ("UG", "Uganda"),
            ("UA", "Ukraine"),
            ("AE", "United Arab Emirates"),
            ("UK", "United Kingdom"),
            ("UY", "Uruguay"),
            ("UZ", "Uzbekistan"),
            ("VU", "Vanuatu"),
            ("VA", "Vatican City State"),
            ("VE", "Venezuela"),
            ("VN", "Viet Nam"),
            ("VG", "Virgin Islands (British)"),
            ("VI", "Virgin Islands (U.S.)"),
            ("YE", "Yemen"),
            ("YU", "Yugoslavia"),
            ("ZR", "Zaire"),
            ("ZM", "Zambia"),
            ("ZW", "Zimbabwe"),
        ]
        return random.choice(countries)