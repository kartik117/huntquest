// CI/CD pipeline for HuntQuest -- build, test, build images, push to ECR,
// deploy to EKS. GitHub Actions (.github/workflows/ci.yml) is what actually
// gates pushes to this repo day-to-day; this Jenkinsfile is the artifact
// that demonstrates the Jenkins half of the resume bullet and is written to
// run for real against a Jenkins controller with Docker + AWS credentials
// configured, not just to look plausible. The ECR/EKS stages detect missing
// AWS credentials and skip with a clear message rather than fail the whole
// pipeline, the same graceful-degradation idea used for the optional LLM
// client and SMTP mailer elsewhere in this batch of projects.
pipeline {
    agent any

    environment {
        AWS_REGION   = 'us-west-2'
        ECR_REGISTRY = "${env.AWS_ACCOUNT_ID ?: ''}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend: install & lint') {
            steps {
                dir('backend') {
                    sh 'pip install -e ".[dev]"'
                    sh 'ruff check src tests'
                }
            }
        }

        stage('Backend: test') {
            steps {
                dir('backend') {
                    sh 'pytest -v --junitxml=test-results.xml'
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }

        stage('Frontend: install, lint, build') {
            steps {
                dir('frontend') {
                    sh 'npm ci'
                    sh 'npm run lint'
                    sh 'npm run build'
                }
            }
        }

        stage('Build images') {
            steps {
                sh "docker build -t huntquest-api:${IMAGE_TAG} ./backend"
                sh "docker build -t huntquest-frontend:${IMAGE_TAG} ./frontend"
            }
        }

        stage('Push to ECR') {
            when {
                branch 'main'
            }
            steps {
                script {
                    if (!env.AWS_ACCOUNT_ID) {
                        echo 'AWS_ACCOUNT_ID not configured on this Jenkins instance -- skipping ECR push. ' +
                             'Configure it (and AWS credentials) to push real images.'
                        return
                    }
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        docker tag huntquest-api:${IMAGE_TAG} ${ECR_REGISTRY}/huntquest-api:${IMAGE_TAG}
                        docker tag huntquest-frontend:${IMAGE_TAG} ${ECR_REGISTRY}/huntquest-frontend:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/huntquest-api:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/huntquest-frontend:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Deploy to EKS') {
            when {
                branch 'main'
            }
            steps {
                script {
                    if (!env.AWS_ACCOUNT_ID) {
                        echo 'AWS_ACCOUNT_ID not configured on this Jenkins instance -- skipping EKS deploy.'
                        return
                    }
                    sh """
                        aws eks update-kubeconfig --region ${AWS_REGION} --name huntquest
                        kubectl -n huntquest delete job huntquest-migrate --ignore-not-found
                        kubectl apply -f k8s/migrate-job.yaml
                        kubectl -n huntquest wait --for=condition=complete --timeout=120s job/huntquest-migrate
                        kubectl -n huntquest set image deployment/huntquest-api api=${ECR_REGISTRY}/huntquest-api:${IMAGE_TAG}
                        kubectl -n huntquest set image deployment/huntquest-frontend frontend=${ECR_REGISTRY}/huntquest-frontend:${IMAGE_TAG}
                        kubectl -n huntquest rollout status deployment/huntquest-api --timeout=120s
                        kubectl -n huntquest rollout status deployment/huntquest-frontend --timeout=120s
                    """
                }
            }
        }
    }

    post {
        always {
            sh 'docker image prune -f --filter "label=stage=build" || true'
        }
    }
}
