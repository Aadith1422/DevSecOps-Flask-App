
pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
    }

    environment {
        PYTHONUNBUFFERED = '1'
        VENV_DIR = '.jenkins-venv'
        IMAGE_NAME = 'devsecops-flask-app'
    }

    stages {

        // STAGE 1: GITHUB CHECKOUT
        stage('Checkout Source Code') {
            steps {
                checkout scm

                sh '''
                    set -e
                    git log -1 --oneline
                '''
            }
        }

        // STAGE 2: PYTHON ENVIRONMENT
        stage('Setup Python Environment') {
            steps {
                sh '''
                    set -e

                    python3 -m venv "${VENV_DIR}"

                    "${VENV_DIR}/bin/python" -m pip install --upgrade pip

                    "${VENV_DIR}/bin/python" -m pip install \
                        -r requirements.txt

                    "${VENV_DIR}/bin/python" -m pip install pytest-cov

                    echo "Python environment ready"
                '''
            }
        }

        // STAGE 3: UNIT TESTING AND COVERAGE
        stage('Unit Tests and Coverage') {
            steps {
                withEnv([
                    'SECRET_KEY=jenkins-ci-test-only-secret-key-not-for-production'
                ]) {
                    sh '''
                        set -e

                        "${VENV_DIR}/bin/python" -m pytest tests/ -v \
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

        // STAGE 4: SONARQUBE CLOUD SAST
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

        // STAGE 5: TRIVY SCA REPORT
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

        // STAGE 6: TRIVY SCA SECURITY GATE
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

                    echo "Trivy SCA security gate passed"
                '''
            }
        }

        // STAGE 7: SOFTWARE BILL OF MATERIALS
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

        // STAGE 8: DOCKER IMAGE BUILD
        stage('Docker Image Build') {
            steps {
                sh '''
                    set -e

                    docker build \
                        -t "${IMAGE_NAME}:${BUILD_NUMBER}" \
                        .

                    echo "Docker image built successfully"
                    docker image ls "${IMAGE_NAME}"
                '''
            }
        }

        // STAGE 9: TRIVY DOCKER IMAGE REPORT
        stage('Trivy Docker Image Scan') {
            steps {
                sh '''
                    set -e

                    trivy image \
                        --scanners vuln \
                        --severity HIGH,CRITICAL \
                        --format json \
                        --output trivy-image-report.json \
                        --exit-code 0 \
                        "${IMAGE_NAME}:${BUILD_NUMBER}"

                    echo "Docker image vulnerability report generated"
                '''
            }
        }

        // STAGE 10: DOCKER IMAGE SECURITY GATE
        stage('Trivy Docker Image Security Gate') {
            steps {
                sh '''
                    set -e

                    trivy image \
                        --scanners vuln \
                        --severity CRITICAL \
                        --exit-code 1 \
                        "${IMAGE_NAME}:${BUILD_NUMBER}"

                    echo "Docker image security gate passed"
                '''
            }
        }

        // STAGE 11: DEPLOY FLASK TO STAGING
        stage('Deploy Flask to Staging') {
            steps {
                sh '''
                    set -e

                    echo "Deploying Flask application to staging..."

                    docker rm -f devsecops-flask-staging \
                        2>/dev/null || true

                    docker run -d \
                        --name devsecops-flask-staging \
                        --restart unless-stopped \
                        -p 127.0.0.1:5050:5000 \
                        -e SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
                        "${IMAGE_NAME}:${BUILD_NUMBER}"

                    echo "Waiting for staging health check..."

                    HEALTHY=0

                    for i in $(seq 1 30); do
                        if docker exec devsecops-flask-staging \
                            python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)" \
                            >/dev/null 2>&1; then

                            HEALTHY=1
                            break
                        fi

                        sleep 2
                    done

                    if [ "$HEALTHY" -ne 1 ]; then
                        echo "Staging deployment failed"
                        docker logs devsecops-flask-staging
                        exit 1
                    fi

                    echo "Staging deployment successful"
                    docker ps --filter name=devsecops-flask-staging
                '''
            }
        }

        // STAGE 12: POST-DEPLOYMENT DAST
        stage('OWASP ZAP Post-Deployment DAST') {
            steps {
                sh '''
                    set -e

                    echo "Starting OWASP ZAP post-deployment DAST scan..."

                    test -f scripts/run-zap-staging.sh

                    bash scripts/run-zap-staging.sh

                    echo "Generated ZAP reports:"
                    ls -lh zap-reports/

                    test -s zap-reports/zap-report.html
                    test -s zap-reports/zap-report.json
                    test -s zap-reports/zap-report.md

                    echo "Post-deployment DAST scan completed"
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'coverage.xml,trivy-report.json,trivy-image-report.json,sbom.cdx.json,zap-reports/*',
                allowEmptyArchive: true
            )
        }

        success {
            echo '''
                ==========================================
                  DEVSECOPS PIPELINE SUCCESSFUL
                ==========================================
                GitHub Checkout       : SUCCESS
                Python Environment    : SUCCESS
                Unit Tests            : SUCCESS
                SonarQube Cloud SAST   : COMPLETED
                Trivy SCA             : PASSED
                Syft SBOM             : GENERATED
                Docker Image Build    : SUCCESS
                Trivy Image Scan      : PASSED
                Trivy Image Gate      : PASSED
                Staging Deployment    : SUCCESS
                OWASP ZAP DAST        : COMPLETED
                ZAP Reports           : GENERATED
                ==========================================
            '''
        }

        failure {
            echo '''
                ==========================================
                  DEVSECOPS PIPELINE FAILED
                ==========================================
                  Check Jenkins Console Output for details.
                ==========================================
            '''
        }
    }
}
