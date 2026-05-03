pipeline {
  agent any

  stages {
    stage('Install Python Dependencies') {
      steps {
        bat 'python -m pip install -r requirements.txt'
      }
    }

    stage('Run Tests') {
      steps {
        bat 'python -m pytest -q'
      }
    }

    stage('Build Docker Image') {
      steps {
        bat 'docker build -t irrigation-api:latest .'
      }
    }
  }
}
