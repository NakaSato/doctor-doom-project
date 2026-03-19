# Notify Service

**Port:** 8003

Handles notifications via email, SMS, webhooks, and push notifications.

## Features

- Email notifications (SMTP/SendGrid)
- SMS alerts (Twilio)
- Slack webhook integration
- Push notifications (FCM)
- Automatic alerts for critical defects

## Endpoints

- `POST /api/v1/notifications` - Send notification
- `POST /api/v1/alerts/defect` - Alert on defect detection
- `POST /api/v1/alerts/report` - Notify when report ready

## Redis Streams

- Reads from: `defect:detected` (for automatic alerts)

## Configuration

Set environment variables:
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `SLACK_WEBHOOK_URL`
