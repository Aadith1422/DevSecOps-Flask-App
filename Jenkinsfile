
pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
    }

    environment {
        SONAR_SCANNER_HOME = tool 'SonarScanner'
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
    }

    post {
        success {
            echo 'DevSecOps CI + SonarQube SAST passed!'
        }

        failure {
            echo 'Pipeline failed. Check Jenkins console output.'
        }

        always {
            archiveArtifacts(
                artifacts: 'coverage.xml',
                allowEmptyArchive: true
            )
        }
    }
}
