# CloudHER AI Smart Dashboard

<p align="center">
  <strong>CloudHER by WIICA — Final Capstone Project</strong><br>
  <em>Serverless AI Document Analysis + Contact Form + Live Dashboard</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AWS-CloudFormation-orange?logo=amazon-aws" alt="AWS CloudFormation">
  <img src="https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws" alt="AWS Lambda">
  <img src="https://img.shields.io/badge/AWS-API%20Gateway-orange?logo=amazon-aws" alt="API Gateway">
  <img src="https://img.shields.io/badge/AI-Groq-blue" alt="Groq AI">
  <img src="https://img.shields.io/badge/Status-Final%20Project%20Completed-success" alt="Status">
</p>

---

## Table of Contents

- [CloudHER AI Smart Dashboard](#cloudher-ai-smart-dashboard)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Architecture](#architecture)
  - [Features](#features)
  - [Tech Stack](#tech-stack)
  - [Prerequisites](#prerequisites)
  - [Project Structure](#project-structure)
  - [Deployment Guide](#deployment-guide)
    - [1. Create an S3 bucket for Lambda packages](#1-create-an-s3-bucket-for-lambda-packages)
    - [2. Package and upload the Lambda functions](#2-package-and-upload-the-lambda-functions)
    - [3. Deploy the CloudFormation stack](#3-deploy-the-cloudformation-stack)
    - [4. Upload the website to S3](#4-upload-the-website-to-s3)
  - [How the Application Works](#how-the-application-works)
  - [Troubleshooting Notes](#troubleshooting-notes)
    - [1. AI Analysis returned “The AI analysis service returned an error”](#1-ai-analysis-returned-the-ai-analysis-service-returned-an-error)
    - [2. Contact form failed with AccessDenied on `ses:SendEmail`](#2-contact-form-failed-with-accessdenied-on-sessendemail)
    - [3. Live dashboard stuck on “Loading submissions…”](#3-live-dashboard-stuck-on-loading-submissions)
    - [4. SES Sandbox restriction](#4-ses-sandbox-restriction)
  - [Deliverables Checklist](#deliverables-checklist)
  - [Skills Demonstrated](#skills-demonstrated)
  - [What I Learned](#what-i-learned)
  - [Cleanup](#cleanup)
  - [Author](#author)
  - [Acknowledgements](#acknowledgements)
  - [License](#license)

---

## Overview

This is the **final capstone project** for the CloudHER by WIICA mentorship program.

The **CloudHER AI Smart Dashboard** is a fully serverless web application that allows users to:

1. Upload a text document and receive an AI-generated summary (powered by Groq)
2. Send a contact message and receive an automatic confirmation email
3. View every submission in real time on a live dashboard

Everything is deployed with **AWS CloudFormation** and runs on:

- API Gateway
- Three Lambda functions
- DynamoDB
- S3 (static website)
- SES (email)
- VPC with private subnets + NAT Gateway

The goal was to build a production-style serverless application that combines infrastructure-as-code, secure networking, AI integration, and a clean frontend — all while staying within free-tier limits where possible.

---

## Architecture

```
                        Internet
                           │
                    Amazon API Gateway
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   POST /analyze     POST /contact      GET /submissions
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Analyzer      │  │ Contact       │  │ Dashboard     │
│ Lambda        │  │ Lambda        │  │ Lambda        │
│ (Groq AI)     │  │ (SES + DB)    │  │ (Scan table)  │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    DynamoDB Table
               (cloudher-dashboard-submissions)
                           │
                    S3 Static Website
               (index.html + error.html)
```

All three Lambda functions run inside **private subnets** and reach the internet through a **NAT Gateway**. DynamoDB traffic stays private via a VPC Gateway Endpoint.

---

## Features

| Feature | Description |
|---------|-------------|
| **AI Document Summarizer** | Upload `.txt` / `.md` files → Groq AI returns a concise summary |
| **Contact Form** | Sends confirmation email to the user + notification to the owner via Amazon SES |
| **Live Submissions Dashboard** | Automatically refreshes and shows every analysis + contact message |
| **Serverless Architecture** | No servers to manage — fully event-driven |
| **Infrastructure as Code** | Entire stack deployed with one CloudFormation template |
| **Secure Networking** | Lambdas in private subnets, least-privilege IAM roles |

---

## Tech Stack

- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Backend**: AWS Lambda (Python 3.12)
- **API**: Amazon API Gateway (HTTP API)
- **Database**: Amazon DynamoDB
- **Email**: Amazon SES
- **AI**: Groq API (`openai/gpt-oss-20b`)
- **Infrastructure**: AWS CloudFormation
- **Networking**: VPC, Private Subnets, NAT Gateway, VPC Endpoints
- **Storage**: Amazon S3 (static website hosting)

---

## Prerequisites

- AWS account
- AWS CLI configured
- A Groq API key ([console.groq.com](https://console.groq.com))
- At least one email address verified in Amazon SES
- Basic familiarity with the AWS console

---

## Project Structure

```text
CloudHER-AI-Smart-Dashboard/
│
├── Infrastructure/
│   └── main-template.yaml          # Full CloudFormation stack
│
├── Lambda/
│   ├── analyzer_handler.py         # Calls Groq AI
│   ├── contact_handler.py          # Saves to DynamoDB + sends SES emails
│   ├── dashboard_handler.py        # Scans DynamoDB for live dashboard
│   ├── analyzer_function.zip
│   ├── contact_function.zip
│   └── dashboard_function.zip
│
├── Website/
│   ├── index.html                  # Main frontend
│   └── error.html
│
├── scripts/
│   └── package_lambdas.sh          # Helper script to zip & upload Lambdas
│
├── Screenshots/                    # Evidence of the working application
│
├── README.md
├── .gitignore
└── LICENSE
```

---

## Deployment Guide

### 1. Create an S3 bucket for Lambda packages

```bash
aws s3 mb s3://YOUR-DEPLOYMENT-BUCKET-NAME
```

### 2. Package and upload the Lambda functions

```bash
cd scripts
chmod +x package_lambdas.sh
./package_lambdas.sh YOUR-DEPLOYMENT-BUCKET-NAME
```

### 3. Deploy the CloudFormation stack

```bash
aws cloudformation deploy \
  --template-file Infrastructure/main-template.yaml \
  --stack-name cloudher-ai-smart-dashboard \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    LambdaDeploymentBucket=YOUR-DEPLOYMENT-BUCKET-NAME \
    GroqApiKey=YOUR_GROQ_API_KEY \
    SenderEmail=your-verified-email@gmail.com \
    RecipientEmail=your-verified-email@gmail.com
```

### 4. Upload the website to S3

Upload `Website/index.html` and `Website/error.html` to the website bucket created by the stack and enable static website hosting.

---

## How the Application Works

1. User uploads a document on the website
2. Frontend sends the text to `POST /analyze`
3. Analyzer Lambda calls Groq AI and saves the summary to DynamoDB
4. User fills the contact form → `POST /contact`
5. Contact Lambda saves the message and sends two emails via SES
6. Live dashboard calls `GET /submissions` every few seconds and displays everything

---

## Troubleshooting Notes

### 1. AI Analysis returned “The AI analysis service returned an error”
**Cause:** Groq blocked the request because of the default Python `User-Agent`.  
**Fix:** Added a custom `User-Agent` header in `analyzer_handler.py`.

### 2. Contact form failed with AccessDenied on `ses:SendEmail`
**Cause:** IAM role only allowed one specific email identity.  
**Fix:** Updated the role policy to allow `ses:SendEmail` on `*`.

### 3. Live dashboard stuck on “Loading submissions…”
**Cause:** DynamoDB returns numbers as `Decimal`, which `json.dumps` cannot serialize.  
**Fix:** Added a custom JSON encoder in `dashboard_handler.py`.

### 4. SES Sandbox restriction
While the account is in SES sandbox, emails can only be sent to verified addresses. Request production access when ready.

---

## Deliverables Checklist

- [x] Full CloudFormation template
- [x] Three working Lambda functions
- [x] S3 static website
- [x] AI document summarization working
- [x] Contact form + SES emails working
- [x] Live submissions dashboard working
- [x] VPC with private subnets + NAT Gateway
- [x] Least-privilege IAM roles
- [x] Screenshots of the running application
- [x] Clean GitHub repository with documentation

---

## Skills Demonstrated

- Infrastructure as Code with CloudFormation
- Serverless architecture (Lambda + API Gateway)
- Secure networking (VPC, private subnets, NAT Gateway, VPC Endpoints)
- DynamoDB design and querying
- Amazon SES integration
- Third-party AI API integration (Groq)
- Frontend ↔ Backend communication
- Debugging with CloudWatch Logs
- IAM least-privilege policies
- End-to-end project delivery

---

## What I Learned

- How to design a complete serverless application from scratch
- Why Lambdas in private subnets need a NAT Gateway for outbound internet access
- How DynamoDB `Decimal` types break normal JSON serialization
- How Cloudflare / Groq can block requests based on User-Agent
- The importance of reading CloudWatch logs instead of guessing
- How SES sandbox mode affects real-world testing
- How to structure a professional final project repository

---

## Cleanup

To avoid ongoing charges:

```bash
aws cloudformation delete-stack --stack-name cloudher-ai-smart-dashboard
```

Also delete:
- The Lambda deployment S3 bucket
- Any leftover NAT Gateway / Elastic IP if the stack does not remove them automatically

---

## Author

**Daniel Nzioki Musyoka**

[![GitHub](https://img.shields.io/badge/GitHub-Daniel059-181717?logo=github)](https://github.com/Daniel059)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Daniel%20Nzioki%20Musyoka-0A66C2?logo=linkedin)](https://www.linkedin.com/in/daniel-nzioki-musyoka)

---

## Acknowledgements

This project was completed as the **final milestone** of the **CloudHER by WIICA** mentorship program.

Special thanks to:
- **Rajpreet Gill** — Mentor
- **Paula Ali Wakabi (Miss. Cloud)** — Founder, WIICA
- Women Innovating in Cloud Africa (WIICA)

---

## License

This project is intended for educational and portfolio purposes.
```

---
