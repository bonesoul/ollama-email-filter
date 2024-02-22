import re
from inbox.action.message import MessageAction
from email.message import Message
from email.header import decode_header
from bs4 import BeautifulSoup
import json

import ollama

def consolidate_whitespace(text):
    # Normalize Windows style newlines to Unix style
    text = text.replace('\r', '\n')
    # Replace multiple spaces and tabs with a single space
    text = re.sub(r'[\s\t]+', ' ', text)
    # Remove spaces at the beginning of each line
    text = re.sub(r'(?m)^\s+', '', text)
    # Remove spaces at the end of each line
    text = re.sub(r'(?m)\s+$', '', text)
    text = re.sub(r'\s*\n\s*', '\n', text)
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    return text

class SpamClassifyAction(MessageAction):
    def __init__(self, provider):
        super().__init__(provider)
    
    def extract_text(self, email_message: Message):
        body = ''
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                body += part.get_payload()

        if (body == ''):
            html_body = ''
            for part in email_message.walk():
                if part.get_content_type() == 'text/html':
                    html_body += part.get_payload()
                    break
            
            body = BeautifulSoup(html_body, 'html.parser').get_text()

        return body

    def processMessage(self, email_message: Message):
        # Step 1: Check if you have ever emailed this person before
        if self.provider.has_emailed_before(email_message['From']):
            print(f"Previously emailed {email_message['From']}, skipping.")
            return

        # # Step 2: Check if the email has been labeled as "AI Email Spam" or "Processed by AI Email Filter"
        # labels = self.provider.get_message_labels(email_message)
        # if 'AI Email Spam' in labels or 'Processed by AI Email Filter' in labels:
        #     print(f"Email already labeled as 'AI Email Spam' or 'Processed by AI Email Filter', skipping.")
        #     return

        # Step 3: Send the email content to the chat model for classification
        email_content = self.extract_text(email_message)

        email_content = consolidate_whitespace(email_content)[:1000]  # Limit the email content to 5000 characters
        
        # json_schema = {
        #     "answer": "boolean"
        # }

        # dumps = json.dumps(json_schema, indent=2)

        # prompt = ChatPromptTemplate.from_messages([
        #     ("system", "You are a highly intelligent AI trained to identify sales outreach emails. You only respond in JSON with format {{\"isSalesOutreach\": \"boolean\"}}."),
        #     ("human", "Is this email an unsolicited sales outreach? Respond in JSON with format {{\"isSalesOutreach\": \"boolean\"}}\n\nEmail:\n###{email_content}\n###\n")
        # ])
        # chain = prompt | self.chat_model | output_parser
        # response = chain.invoke({"email_content": email_content, "dumps": dumps})
        prompt='''
You are a highly intelligent AI trained to identify sales outreach or promotion emails.
You only respond in JSON with format {"isSalesOrPromotion": "boolean"}. 

So for example the following email:
```email
Hi, I'm reaching out to see if you'd be interested in our new product.
```

```answer
{
"isSalesOrPromotion": true
}
```answer

Classify the email below:
```email
'''
        prompt += email_content
        prompt += "\n```"
        
        print(prompt)

        output = ollama.chat(model='mistral', messages=[{
            'role': 'user',
            'content': prompt
        }])
        # Extract everything between curly braces, including the braces
        
        print(f"\033[41;37m{email_message['From']} {output['message']['content']}\033[0m")
        
        response = output['message']['content']
        is_spam = False

        # Define the regex pattern to extract the JSON object, accounting for any valid combination of whitespaces
        json_pattern = re.compile(r'\{\s*"isSalesOrPromotion"\s*:\s*(true|false)\s*\}')
        # Search for the pattern in the response
        match = json_pattern.search(response)
        if match:
            # Parse the JSON object
            is_spam_json = json.loads(match.group())
            is_spam = is_spam_json.get("isSalesOrPromotion", False)

        # Step 4 & 5: Label and possibly archive the message based on the chat model's response
        if is_spam:
            print("Message labeled as 'AI Email Spam' and archived.")
            # self.provider.label_message(email_message, ['AI Email Spam'])
            # self.provider.archive_message(email_message)
        else:
            print("Message labeled as 'Processed by AI Email Filter'.")
            # self.provider.label_message(email_message, ['Processed by AI Email Filter'])
