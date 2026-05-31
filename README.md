# SecOps AI Agent: Event-Driven Serverless Log Analyzer

An automated, cloud-native Security Operations (SecOps) solution designed to monitor, parse, and respond to infrastructure anomalies in real-time using an event-driven architecture on AWS.

## 📐 Architecture Overview

The system is fully decoupled and built around serverless computing principles, ensuring high availability and zero cost during idle times.

* **Ingestion:** Audit logs are uploaded securely to an **Amazon S3** bucket.
* **Trigger:** S3 Event Notifications automatically detect new log files and invoke the analysis engine asynchronously.
* **Compute (AI Agent):** An **AWS Lambda** function written in Python 3.12 parses the raw log stream in milliseconds using optimized Regular Expressions (RegEx). It evaluates incoming traffic against specific security rules.
* **Notification:** If threats are discovered, the agent acts as an asynchronous producer, publishing a structured JSON payload to an **Amazon SNS** topic, which instantly alerts DevOps engineers via email routing.

## 🛠️ Security Analysis Rules Defined
* **Rule 1 (Directory Scanning):** Detects unauthorized recon attempts targeting high-value paths (e.g., `/admin`, `/config`, `/phpmyadmin`).
* **Rule 2 (Anomalous Network Activity):** Monitors unexpected `403 Forbidden` status responses indicating perimeter probes.

## 🚀 Deployment & IaC
The entire ecosystem (IAM roles, Least-Privilege inline policies, S3 triggers, Lambda variables, and SNS configurations) is defined declaratively using **Terraform** for Infrastructure as Code (IaC), promoting seamless cross-region delivery and network segmentation principles.