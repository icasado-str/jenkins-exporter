from prometheus_client.core import (GaugeMetricFamily, CounterMetricFamily)
import time

current_milli_time = lambda: int(round(time.time() * 1000))
timestamp_24h_ago = lambda: current_milli_time() - 24 * 3600 * 1000
timestamp_15days_ago = lambda: current_milli_time() - 15 * 24 * 3600 * 1000

def make_metrics(jobs):

    list_metrics = []
    list_jobs = jobs.get_list_jobs()

    # Total job
    metric = GaugeMetricFamily(
        'jenkins_jobs_total',
        'Total job in Jenkins',
        labels=None
    )

    metric.add_metric(
        labels=[],
        value=jobs.get_total_jobs()
    )

    list_metrics.append(metric)

    # Total build of a job
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_job_builds_total',
        'Total builds of a job',
        labels=['job_name']
    )
    for job_id in list_jobs:  # job_id == job['full_name']
        metric.add_metric(
            labels=[job_id],
            value=jobs.get_total_builds(job_id)
        )

    list_metrics.append(metric)

    # Total consecutive failed of a job
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_job_fail_consecutively',
        'The number of times the last consecutive failure build of a job',
        labels=['job_name']
    )
    for job_id in list_jobs:
        metric.add_metric(
            labels=[job_id],
            value=jobs.get_total_fail_consecutively(job_id)
        )

    list_metrics.append(metric)

    # Total building jobs
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_jobs_building_total',
        'Total building jobs',
        labels=None
    )
    metric.add_metric(
        labels=[],
        value=jobs.get_total_building_jobs()
    )

    list_metrics.append(metric)

    # The building duration of a building job
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_jobs_building_time_seconds',
        'The running duration of a building job',
        labels=['job_name', 'status']
    )
    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        building_duration = jobs.get_building_duration(job_id)
        if building_duration > 0:
            metric.add_metric(
                labels=[job_id, 'building'],
                value=building_duration
            )
        else:
            if jobs.get_total_builds(job_id) == 0:
                metric.add_metric(
                    labels=[job_id, 'not_yet_built'],
                    value=0
                )
            else:
                metric.add_metric(
                    labels=[job_id, 'not_building'],
                    value=0
                )

    list_metrics.append(metric)

    # CUSTOM METRICS
    # Custom building time milliseconds
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_jobs_building_time_milliseconds_with_estimation',
        'The running duration of a building job with its estimation',
        labels=['job_name', 'status', 'number', 'estimatedDuration', 'tenant', 'repo', 'branch']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        splitted_full_name = job['full_name'].split("/")
        tenant = splitted_full_name[0]
        repo = splitted_full_name[1]
        branch = splitted_full_name[2]
        last_build = job['last_build']
        duration = int(last_build['duration'])
        if duration > 0:
            metric.add_metric(
                labels=[job_id, last_build['result'], str(last_build['number']), str(last_build['estimatedDuration']),
                        tenant, repo, branch],
                value=duration
            )
        else:
            if jobs.get_total_builds(job_id) == 0:
                metric.add_metric(
                    labels=[job_id, 'NOT_YET_BUILT', str(last_build['number']), str(last_build['estimatedDuration']),
                            tenant, repo, branch],
                    value=0
                )
            else:
                metric.add_metric(
                    labels=[job_id, 'BUILDING', str(last_build['number']), str(last_build['estimatedDuration']),
                            tenant, repo, branch],
                    value=current_milli_time() - last_build['timestamp']
                )

    list_metrics.append(metric)

    # Custom building % of time upper estimated
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_jobs_building_percent_time_over_estimation',
        'The percent time of the last building job over its estimation',
        labels=['job_name', 'status', 'number', 'estimatedDuration', 'duration', 'tenant', 'repo', 'branch']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        splitted_full_name = job['full_name'].split("/")
        tenant = splitted_full_name[0]
        repo = splitted_full_name[1]
        branch = splitted_full_name[2]
        last_build = job['last_build']
        duration = int(last_build['duration'])
        if duration > 0:
            metric.add_metric(
                labels=[job_id, last_build['result'], str(last_build['number']), str(last_build['estimatedDuration']),
                        str(last_build['duration']), tenant, repo, branch],
                value=(duration / last_build['estimatedDuration']) * 100 - 100
            )
        else:
            if jobs.get_total_builds(job_id) == 0:
                metric.add_metric(
                    labels=[job_id, 'NOT_YET_BUILT', str(last_build['number']), str(last_build['estimatedDuration']),
                            str(last_build['duration']), tenant, repo, branch],
                    value=0
                )
            else:
                metric.add_metric(
                    labels=[job_id, 'BUILDING', str(last_build['number']), str(last_build['estimatedDuration']),
                            str(last_build['duration']), tenant, repo, branch],
                    value=(current_milli_time() - last_build['timestamp']) / last_build['estimatedDuration'] * 100 - 100
                )

    list_metrics.append(metric)

    # Builds by repo
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_builds_by_repo_and_tenant_last24h',
        'The number of builds by status, tenant, repo and branch',
        labels=['job_name', 'status', 'tenant', 'repo', 'branch']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        splitted_full_name = job['full_name'].split("/")
        tenant = splitted_full_name[0]
        repo = splitted_full_name[1]
        branch = splitted_full_name[2]
        builds = job['builds']['info']
        builds_last_15days = list(filter(lambda x: x['timestamp'] > timestamp_15days_ago(), builds))
        builds_last_24h = list(filter(lambda x: x['timestamp'] > timestamp_24h_ago(), builds))
        aborted = sum(map(lambda x: x['result'] == "ABORTED", builds_last_24h))
        success = sum(map(lambda x: x['result'] == "SUCCESS", builds_last_24h))
        #success = sum(map(lambda x: x['result'] == "SUCCESS" and not x['building'], builds_last_24h))
        #success_but_waiting_to_response = sum(map(lambda x: x['result'] == "SUCCESS" and x['building'], builds_last_24h))
        failure = sum(map(lambda x: x['result'] == "FAILURE", builds_last_24h))
        not_built = sum(map(lambda x: x['result'] == "NOT_BUILT", builds_last_24h))
        #unknown = sum(map(lambda x: x['result'] is None, builds_last_24h))
        #building = sum(map(lambda x: x['building'] and x['result'] is None, builds_last_24h))
        total = len(builds)
        #total = len(builds_last_15days)
        # If we have builds during the last week we add its stats
        if total > 0:
            metric.add_metric(
                labels=[job_id, 'ABORTED', tenant, repo, branch],
                value=aborted
            )
            metric.add_metric(
                labels=[job_id, 'SUCCESS', tenant, repo, branch],
                value=success
            )
            metric.add_metric(
                labels=[job_id, 'FAILURE', tenant, repo, branch],
                value=failure
            )
            metric.add_metric(
                labels=[job_id, 'NOT_BUILT', tenant, repo, branch],
                value=not_built
            )

    list_metrics.append(metric)

    # Total builds by tenant, repo and branch
    metric = None
    metric = CounterMetricFamily(
        'jenkins_total_builds_by_tenant_repo_and_branch',
        'The total number of builds by branch',
        labels=['tenant', 'repo', 'branch']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        splitted_full_name = job['full_name'].split("/")
        tenant = splitted_full_name[0]
        repo = splitted_full_name[1]
        branch = splitted_full_name[2]
        builds = job['builds']['info']
        total = len(builds)
        metric.add_metric(
            labels=[tenant, repo, branch],
            value=total
        )

    list_metrics.append(metric)

    # Jobs waiting for an user action
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_duration_of_jobs_waiting_for_an_user_action',
        'How long are the current jobs waiting for an user action to continue',
        labels=['job_name', 'status', 'tenant', 'repo', 'branch', 'number']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        splitted_full_name = job['full_name'].split("/")
        tenant = splitted_full_name[0]
        repo = splitted_full_name[1]
        branch = splitted_full_name[2]
        builds = job['builds']['info']
        buildings = list(filter(lambda x: x['building'], builds))

        for building in buildings:
            metric.add_metric(
                labels=[job_id, str(building['result']), tenant, repo, branch, str(building['number'])],
                value=current_milli_time() - building['timestamp']
            )

    list_metrics.append(metric)
    return list_metrics
