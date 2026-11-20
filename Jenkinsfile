pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
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
                    .jenkins-venv/bin/python -m pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                withEnv([
                    'SECRET_KEY=jenkins-ci-test-key-not-for-production'
                ]) {
                    sh '''
                        .jenkins-venv/bin/python -m pytest tests/ -v
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Flask CI pipeline passed!'
        }

        failure {
            echo 'Flask CI pipeline failed. Check console output.'
        }
    }
}