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

resource "aws_lambda_permission" "allow_eventbridge_api" {
  statement_id  = "AllowExecutionFromEventBridge_API_${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_extractor_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cron_trigger.arn
}

resource "aws_lambda_permission" "allow_eventbridge_sftp" {
  statement_id  = "AllowExecutionFromEventBridge_SFTP_${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = var.sftp_lambda_extractor_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cron_trigger.arn
}