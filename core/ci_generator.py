"""
CI/CD Configuration Generator
Generates workflow files for GitHub Actions, Jenkins, etc.

Phase 3: 매트릭스 브라우저 빌드 + Slack 알림 + Allure 리포트 지원
"""


class CIGenerator:
    def generate_github_actions(self, browser_type="chrome", slack_webhook=False):
        """
        Generate GitHub Actions workflow content for running Pytest

        Args:
            browser_type: 기본 브라우저 (매트릭스에서 사용)
            slack_webhook: Slack 알림 포함 여부

        Returns:
            str: GitHub Actions YAML 워크플로우
        """
        slack_job = ""
        if slack_webhook:
            slack_job = """
  # ── Slack Notification ──
  notify:
    runs-on: ubuntu-latest
    needs: test
    if: always()

    steps:
    - name: Determine Status
      id: status
      run: |
        if [ "${{ needs.test.result }}" == "success" ]; then
          echo "emoji=✅" >> $GITHUB_OUTPUT
          echo "text=All tests passed!" >> $GITHUB_OUTPUT
          echo "color=good" >> $GITHUB_OUTPUT
        else
          echo "emoji=❌" >> $GITHUB_OUTPUT
          echo "text=Some tests failed!" >> $GITHUB_OUTPUT
          echo "color=danger" >> $GITHUB_OUTPUT
        fi

    - name: Send Slack Notification
      if: env.SLACK_WEBHOOK_URL != ''
      uses: slackapi/slack-github-action@v2.0.0
      with:
        webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
        webhook-type: incoming-webhook
        payload: |
          {{
            "text": "${{ steps.status.outputs.emoji }} QA Tests: ${{ steps.status.outputs.text }}",
            "attachments": [
              {{
                "color": "${{ steps.status.outputs.color }}",
                "fields": [
                  {{ "title": "Repository", "value": "${{ github.repository }}", "short": true }},
                  {{ "title": "Branch", "value": "${{ github.ref_name }}", "short": true }}
                ]
              }}
            ]
          }}
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
"""

        return f"""name: QA Automated Tests

on:
  push:
    branches: [ "main", "develop" ]
  pull_request:
    branches: [ "main" ]
  workflow_dispatch:
    inputs:
      browser:
        description: 'Browser to test'
        required: false
        default: '{browser_type}'
        type: choice
        options:
          - chrome
          - firefox

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
        python-version: ["3.9"]

    name: "Test (${{{{ matrix.browser }}}})"

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v5
      with:
        python-version: ${{{{ matrix.python-version }}}}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyyaml

    - name: Setup Chrome
      if: matrix.browser == 'chrome'
      uses: browser-actions/setup-chrome@latest

    - name: Setup Firefox
      if: matrix.browser == 'firefox'
      uses: browser-actions/setup-firefox@latest

    - name: Run Tests (Headless)
      run: |
        python run_tests.py --browser ${{{{ matrix.browser }}}} --headless
      env:
        QA_ATB_DEFAULT_HEADLESS: "true"

    - name: Upload Allure Results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: allure-results-${{{{ matrix.browser }}}}
        path: allure_results/
        retention-days: 14

    - name: Upload Screenshots
      uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: failure-screenshots-${{{{ matrix.browser }}}}
        path: screenshots/
        retention-days: 14
{slack_job}"""

    def generate_jenkinsfile(self):
        """
        Generate Jenkinsfile (Declarative Pipeline)
        """
        return """pipeline {
    agent any

    parameters {
        choice(name: 'BROWSER', choices: ['chrome', 'firefox', 'edge'], description: 'Browser to test')
        booleanParam(name: 'HEADLESS', defaultValue: true, description: 'Run in headless mode')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pyyaml'
            }
        }
        stage('Test') {
            steps {
                sh "python run_tests.py --browser ${params.BROWSER} ${params.HEADLESS ? '--headless' : ''}"
            }
        }
    }
    post {
        always {
            allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
        failure {
            // Slack notification on failure (requires Slack plugin)
            // slackSend(channel: '#qa-automation', message: "Tests failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
            echo "Tests failed! Check Allure report for details."
        }
    }
}
"""
