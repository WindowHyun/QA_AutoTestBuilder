"""
CI/CD Configuration Generator
Generates workflow files for GitHub Actions, Jenkins, etc.
"""

class CIGenerator:
    def generate_github_actions(self, browser_type="chrome"):
        """
        Generate GitHub Actions workflow content for running Pytest
        """
        return f"""name: Automated Tests

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python 3.9
      uses: actions/setup-python@v4
      with:
        python-version: "3.9"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install selenium pytest allure-pytest webdriver-manager pandas openpyxl

    - name: Setup Chrome
      if: "{browser_type}" == "chrome"
      uses: browser-actions/setup-chrome@latest

    - name: Setup Firefox
      if: "{browser_type}" == "firefox"
      uses: browser-actions/setup-firefox@latest

    - name: Run Tests (Headless)
      run: |
        # Run pytest with Allure results
        pytest tests/ --alluredir=allure-results --headless

    - name: Upload Allure Results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: allure-results
        path: allure-results
        retention-days: 5
"""

    def generate_jenkinsfile(self):
        """
        Generate Jenkinsfile (Declarative Pipeline)
        """
        return """pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Test') {
            steps {
                sh 'pytest tests/ --alluredir=allure-results --headless'
            }
        }
    }
    post {
        always {
            allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
        }
    }
}
"""
