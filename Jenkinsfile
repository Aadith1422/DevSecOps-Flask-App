
pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    environment {
        SONAR_SCANNER_HOME = tool 'SonarScanner'
        TRIVY_CACHE_DIR = '/var/lib/jenkins/.cache/trivy'
    }

    stages {
        stage('Checkout GitHub') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv .jenkins-venv
                    .jenkins-venv/bin/python -m pip install --upgrade pip
                    .jenkins-venv/bin/python -m pip install -r requirements.txt
                    .jenkins-venv/bin/python -m pip install pytest-cov
                '''
            }
        }

        stage('Unit Tests and Coverage') {
            steps {
                withEnv([
                    'SECRET_KEY=jenkins-ci-test-key-not-for-production'
                ]) {
                    sh '''
                        .jenkins-venv/bin/python -m pytest tests/ -v \
                          --cov=app \
                          --cov=forms \
                          --cov=models \
                          --cov-report=term-missing \
                          --cov-report=xml:coverage.xml
                    '''
                }
            }
        }

        stage('SonarQube Cloud SAST') {
            steps {
                withSonarQubeEnv('SonarCloud') {
                    sh '''
                        "$SONAR_SCANNER_HOME/bin/sonar-scanner"
                    '''
                }
            }
        }

        stage('Trivy SCA - Vulnerability Report') {
            steps {
                sh '''
                    mkdir -p "$TRIVY_CACHE_DIR"

                    trivy fs \
                      --scanners vuln \
                      --severity HIGH,CRITICAL \
                      --skip-dirs .jenkins-venv \
                      --skip-dirs venv \
                      --skip-dirs .scannerwork \
                      --skip-dirs instance \
                      --format json \
                      --output trivy-report.json \
                      --exit-code 0 \
                      .
                '''
            }
        }

        stage('Trivy SCA - Security Gate') {
            steps {
                sh '''
                    trivy fs \
                      --scanners vuln \
                      --severity CRITICAL \
                      --skip-dirs .jenkins-venv \
                      --skip-dirs venv \
                      --skip-dirs .scannerwork \
                      --skip-dirs instance \
                      --exit-code 1 \
                      .
                '''
            }
        }
    }

    post {
        success {
            echo 'DevSecOps CI, SonarQube SAST and Trivy SCA passed!'
        }

        failure {
            echo 'Pipeline failed. Review the test or security scan results.'
        }

        always {
            archiveArtifacts(
                artifacts: 'coverage.xml,trivy-report.json',
                allowEmptyArchive: true
            )
        }
    }
}
