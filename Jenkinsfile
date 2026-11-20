
pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    environment {
        PYTHONUNBUFFERED = '1'
        VENV_DIR = '.jenkins-venv'
    }

    stages {

        stage('Checkout Source Code') {
            steps {
                checkout scm

                sh '''
                    git log -1 --oneline
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    set -e

                    python3 -m venv .jenkins-venv

                    .jenkins-venv/bin/python -m pip install --upgrade pip

                    .jenkins-venv/bin/python -m pip install -r requirements.txt

                    .jenkins-venv/bin/python -m pip install pytest-cov

                    echo "Python environment ready"
                '''
            }
        }

        stage('Unit Tests and Coverage') {
            steps {
                withEnv([
                    'SECRET_KEY=jenkins-ci-test-only-secret-key-not-for-production'
                ]) {
                    sh '''
                        set -e

                        .jenkins-venv/bin/python -m pytest tests/ -v \
                          --cov=app \
                          --cov=forms \
                          --cov=models \
                          --cov-report=term-missing \
                          --cov-report=xml:coverage.xml

                        echo "Unit tests and coverage completed"
                    '''
                }
            }
        }

        stage('SonarQube Cloud SAST') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarCloud') {
                        sh """
                            "${scannerHome}/bin/sonar-scanner"
                        """
                    }
                }
            }
        }

        stage('Trivy SCA - Vulnerability Report') {
            steps {
                sh '''
                    set -e

                    trivy fs \
                      --scanners vuln \
                      --severity HIGH,CRITICAL \
                      --skip-dirs venv \
                      --skip-dirs .jenkins-venv \
                      --skip-dirs .scannerwork \
                      --skip-dirs instance \
                      --format json \
                      --output trivy-report.json \
                      --exit-code 0 \
                      .

                    echo "Trivy vulnerability report generated"
                '''
            }
        }

        stage('Trivy SCA - Security Gate') {
            steps {
                sh '''
                    set -e

                    trivy fs \
                      --scanners vuln \
                      --severity CRITICAL \
                      --skip-dirs venv \
                      --skip-dirs .jenkins-venv \
                      --skip-dirs .scannerwork \
                      --skip-dirs instance \
                      --exit-code 1 \
                      .

                    echo "Trivy security gate passed"
                '''
            }
        }

        stage('Syft SBOM Generation') {
            steps {
                sh '''
                    set -e

                    /usr/local/bin/syft dir:. \
                      --exclude './venv/**' \
                      --exclude './.jenkins-venv/**' \
                      --exclude './instance/**' \
                      --exclude './.scannerwork/**' \
                      --exclude './.git/**' \
                      -o cyclonedx-json=sbom.cdx.json

                    python3 -m json.tool sbom.cdx.json > /dev/null

                    echo "CycloneDX SBOM generated successfully"

                    ls -lh sbom.cdx.json
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'coverage.xml,trivy-report.json,sbom.cdx.json',
                allowEmptyArchive: true
            )
        }

        success {
            echo 'SUCCESS: CI tests, SonarQube SAST, Trivy SCA and Syft SBOM completed!'
        }

        failure {
            echo 'FAILED: Check Jenkins console output for errors.'
        }
    }
}
