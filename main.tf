provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "secops_logs" {
  bucket = var.bucket_name
}

data "archive_file" "lambda_function_zip" {
  type        = "zip"  
  source_file = "agent_brain.py"
  output_path = "lambda_function_payload.zip"
}  

resource "aws_iam_role" "secops_agent_role" {
  name = "secops-agent-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "sts:AssumeRole"
        Effect   = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "secops-lambda-policy"
  role = aws_iam_role.secops_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.secops_logs.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish" 
        ]
        Resource = aws_sns_topic.secops_alerts.arn
      }
    ]
  })
}

resource "aws_lambda_function" "secops_agent_lambda" {
  filename         = "lambda_function_payload.zip"
  function_name    = "secops-ai-agent-engine"
  runtime          = "python3.12"
  handler          = "agent_brain.lambda_handler"
  role             = aws_iam_role.secops_agent_role.arn
  source_code_hash = data.archive_file.lambda_function_zip.output_base64sha256
  timeout          = 15

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.secops_alerts.arn
    }
  }
}

# 1. Permiso para que S3 pueda invocar a la Lambda
resource "aws_lambda_permission" "allow_s3_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.secops_agent_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.secops_logs.arn
}

# 2. Configuración de la notificación del Bucket de S3
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.secops_logs.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.secops_agent_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3_bucket]
}

# Bloque temporal para subir el log de prueba sin depender de AWS CLI
resource "aws_s3_object" "test_log_upload" {
  bucket = aws_s3_bucket.secops_logs.id
  key    = "ataque_en_vivo_demo1.log"
  source = "${path.module}/audit.log" 
}

# ======= NUEVOS RECURSOS DE LA FASE 4 =======

# 3. Creación del Topic de SNS que faltaba 👈 (¡AQUÍ ESTÁ LA SOLUCIÓN!)
resource "aws_sns_topic" "secops_alerts" {
  name = "secops-agent-alerts-topic"
}

# 4. Suscripción por correo electrónico vinculada al Topic
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.secops_alerts.arn
  protocol  = "email"
  endpoint  = "tu-correo@example.com" 
}