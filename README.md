# Ollama Email Filter - Setup Guide

This guide will help you set up your own Google API client and configure the `gmail_spam_filter.py` to use the Gmail API for filtering or classifying emails using a locally hosted LLM.

## Step 1: Google API Client Creation

1. Go to the [Google Developers Console](https://console.developers.google.com/).
2. Create a new project by clicking on the "New Project" button.
3. Enter a project name and click "Create".
4. Once the project is created, select it from the project list.
5. Navigate to the "Credentials" section in the sidebar.
6. Click on "Create credentials" and select "OAuth client ID".
7. If prompted, configure the consent screen by entering the required information and save it.
8. Select "Web application" as the application type.
9. Add a name for your OAuth 2.0 client and click "Create".
10. Your client ID and client secret will be displayed. Download the JSON file containing these credentials.

## Step 2: Enable Gmail API

1. In the Google Developers Console, select your project.
2. Go to the "Library" section in the sidebar.
3. Search for "Gmail API" and select it.
4. Click on the "Enable" button to enable the Gmail API for your project.

## Step 3: Set Up `gmail_spam_filter.py`

1. Rename the downloaded JSON file containing your OAuth 2.0 credentials to `google_cred.json`.
2. Place the `google_cred.json` file in the `etc` directory located in the same directory as your `gmail_spam_filter.py` script.
3. If the `etc` directory does not exist, create it at the same level as `gmail_spam_filter.py`.


## Contributions Wanted

We are actively seeking contributions to extend the functionality of the Ollama Email Filter. If you're interested in contributing, here are some areas where we'd love your help:

- **Microsoft Outlook Integration**: Develop a provider similar to `GmailProvider` that interfaces with Microsoft Outlook, allowing users to filter and classify emails within Outlook.

- **POP3/IMAP Support**: Implement support for email accounts that use POP3 or IMAP protocols, expanding the range of email services that can be used with our filter.

- **Additional Classification Actions**: Create new actions for classifying emails into categories beyond sales or promotion, such as personal, work-related, or spam from different categories.

If you would like to contribute to any of these areas, please fork the repository, make your changes, and submit a pull request. For more information on how to contribute, please see our `CONTRIBUTING.md` file.
