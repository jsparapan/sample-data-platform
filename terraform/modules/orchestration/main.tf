resource "aws_cloudwatch_event_rule" "cron_trigger" {
  name                = "trigger-uk-extraction-${var.environment}"
  description         = "Dispara a extração a cada 5 minutos"
  schedule_expression = "cron(*/5 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.cron_trigger.name
  target_id = "TriggerLambdaAPI"
  arn       = var.lambda_extractor_arn
}

resource "aws_cloudwatch_event_target" "sftp_lambda_target" {
  rule      = aws_cloudwatch_event_rule.cron_trigger.name
  target_id = "TriggerLambdaSFTP"
  arn       = var.sftp_lambda_extractor_arn
}