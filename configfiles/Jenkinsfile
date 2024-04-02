String moduleName = 'configfiles'
boolean skipRemainingStages = false
def applicationVersion = '12.3.0'
def configFilesCreationTime = ''
def branchName = 'develop'
def configServerTarFileName = ''
def processServerTarFileName = ''

pipeline {
	agent any

	tools {
	    jdk 'Java17'
	}

	environment {
		FOO = 'BAR'
	}
	options {
		skipStagesAfterUnstable()
		buildDiscarder(logRotator(numToKeepStr: '20'))
		disableConcurrentBuilds()
		quietPeriod(30)
	}
	triggers {
		gitlab(
		triggerOnPush: true
		)	
	}
	stages {
		stage('Skip Build') {
			when {
				beforeAgent true
				not {
					anyOf {
						triggeredBy 'UpstreamCause'
						triggeredBy cause: "UserIdCause"
						changeset "${moduleName}/**/*"
					}
				}
			}
			steps {
				echo "NO NEED TO RUN THE BUILD"
				script {
					skipRemainingStages = true
					currentBuild.result = 'NOT_BUILT'
					return
				}
			}
		}
		stage('Verify Caller & Super Caller') {
			when {
				expression {
					!skipRemainingStages
				}
			}
			steps {
				echo 'Verifying the Caller & Its Super Caller Details'
				script {
					if(currentBuild.upstreamBuilds) {
						def callerIsOfsModuleBuilds = false
						def callerCauses = currentBuild.rawBuild.getCauses()
						for(callerCause in callerCauses) {
						def callerCauseDesc = callerCause.shortDescription
						echo "** Build Caller Cause: $callerCauseDesc"
							if(callerCauseDesc.contains('ofs-module-builds') || callerCauseDesc.contains('ofs-patch-builds')) {
								callerIsOfsModuleBuilds = true
								echo "Since Caller Belongs to ofs-module-builds or ofs-patch-builds builds will not be skipped.."
							}
						}

						if(!callerIsOfsModuleBuilds) {
							for(callerCause in callerCauses) {
								def callerCauseDesc = callerCause.shortDescription
								echo "Build Caller Cause: $callerCauseDesc"
								if(callerCause.class.toString().contains("UpstreamCause")){
									for (superCallerCause in callerCause.upstreamCauses) {
										echo "Super Caller Cause: ${superCallerCause.shortDescription}" 
										def superCallerCauseDesc = superCallerCause.shortDescription
										if(superCallerCauseDesc.contains('ofs-module-builds') || superCallerCauseDesc.contains('ofs-patch-builds')) {
											echo  "Skipping this Build, since it's super caller is ofs-module-builds or ofs-patch-builds."
											skipRemainingStages = true
											currentBuild.result = 'NOT_BUILT'
											return
										}
									}
								} else {
									echo "No Super Caller Upstreams exists"
								}
							}
						}
					} else {
						echo "No Caller Upstreams exists"
					}
				}
			}
		}
		stage('Configure Variables') {
			when {
				expression {
					!skipRemainingStages
				}
			}
			steps {
				script {
					properties = readProperties file: 'ofs-version.properties'
					echo "${properties}"
					String version = properties."ofs.version"
					echo " version: $version"
					applicationVersion=version
					branchName=BRANCH_NAME
					echo " applicationVersion: $applicationVersion"
					echo " branchName: $branchName"
								
					def configCreationTime=sh(script:"echo `date +%Y-%m-%d-%H%M` | tr -d '\n'  ", returnStdout: true)
					echo "ConfigFiles Creation Time: $configCreationTime"
					configFilesCreationTime=configCreationTime
				}
			}
		}		
		stage('Build') {
			when {
				expression {
					!skipRemainingStages
				}
			}
			steps {
				echo 'Build Stage'
				echo "${GIT_BRANCH}"
				dir("${moduleName}") {
					sh 'chmod +x ./gradlew'
					sh './gradlew clean build'
				}
			}
		}
		stage("Artifactory Publish"){
			when {
				expression {
					!skipRemainingStages
				}
			}
			//Unlike other Pipelines this needs Artifacts to be Published before building the image.
			steps {
				script {
					dir("${moduleName}") {
						withCredentials([usernamePassword(credentialsId: 'artifactory', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
							sh './gradlew artifactoryPublish -Partifactory_user=$USERNAME -Partifactory_password=$PASSWORD'
						}
					}
				}
			}
		}
		stage('Build Commit History') {
			when {
				expression {
					!skipRemainingStages
				}
			}
			steps {
				script {
					def repoName="ofs"
					def commitId=sh(script: "git log --pretty=oneline | head -1 | cut -d' ' -f1 | tr -d '\n'", returnStdout: true)
					def commitHistoryFolder=sh(script: "echo ${env.commitHistoryLocation} | tr -d '\n'  ", returnStdout: true)
					sh "echo branchName: ${branchName}  : repoName: ${repoName} :   commitId : ${commitId}  : commitHistoryFolder: ${commitHistoryFolder} "

					sh(script: "sudo  ${commitHistoryFolder}/handleBuildCommits.sh ${repoName} ${branchName} ${commitId} '${commitHistoryFolder}' ", returnStdout: true)
				}
			}
		}
	}
	post {
		success {
			echo 'Success'
		}
		failure {
			// $DEFAULT_RECIPIENTS value is fetched from Jenkins -> Configure System -> "Default Recipients"
			emailext body: "${currentBuild.currentResult}: Job ${env.JOB_NAME} build ${env.BUILD_NUMBER}\\n More info at: ${env.BUILD_URL}",
				recipientProviders: [
					[$class: 'CulpritsRecipientProvider'],
					[$class: 'RequesterRecipientProvider']],
				to : '$DEFAULT_RECIPIENTS',
				subject: "Jenkins Build ${currentBuild.currentResult}: Job ${env.JOB_NAME}"
			echo "Failure"
		}
	}
}