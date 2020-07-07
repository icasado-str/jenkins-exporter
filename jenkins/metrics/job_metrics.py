from prometheus_client.core import GaugeMetricFamily
import time

current_milli_time = lambda: int(round(time.time() * 1000))

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

    # Custom building time milliseconds
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_jobs_building_time_milliseconds_with_estimation',
        'The running duration of a building job with its estimation',
        labels=['job_name', 'status', 'number', 'estimatedDuration', 'displayName', 'fullDisplayName']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        last_build = job['last_build']
        duration = int(last_build['duration'])
        if duration > 0:
            metric.add_metric(
                labels=[job_id, last_build['result'], str(last_build['number']), str(last_build['estimatedDuration']), last_build["displayName"], last_build['fullDisplayName']],
                value=duration
            )
        else:
            if jobs.get_total_builds(job_id) == 0:
                metric.add_metric(
                    labels=[job_id, 'NOT_YET_BUILT', str(last_build['number']), str(last_build['estimatedDuration']), last_build["displayName"], last_build['fullDisplayName']],
                    value=0
                )
            else:
                metric.add_metric(
                    labels=[job_id, 'BUILDING', str(last_build['number']), str(last_build['estimatedDuration']), last_build["displayName"], last_build['fullDisplayName']],
                    value=current_milli_time() - last_build['timestamp']
                )

    list_metrics.append(metric)

    # Custom building % of time upper estimated
    metric = None
    metric = GaugeMetricFamily(
        'jenkins_jobs_building_percent_time_over_estimation',
        'The percent time of the last building job over its estimation',
        labels=['job_name', 'status', 'number', 'estimatedDuration', 'duration', 'displayName', 'fullDisplayName']
    )

    for job_id in list_jobs:
        job = jobs.get_job(job_id)
        last_build = job['last_build']
        duration = int(last_build['duration'])
        if duration > 0:
            metric.add_metric(
                labels=[job_id, last_build['result'], str(last_build['number']), str(last_build['estimatedDuration']),
                        str(last_build['duration']), last_build["displayName"], last_build['fullDisplayName']],
                value=(duration / last_build['estimatedDuration']) * 100
            )
        else:
            if jobs.get_total_builds(job_id) == 0:
                metric.add_metric(
                    labels=[job_id, 'NOT_YET_BUILT', str(last_build['number']), str(last_build['estimatedDuration']),
                            str(last_build['duration']), last_build["displayName"], last_build['fullDisplayName']],
                    value=0
                )
            else:
                metric.add_metric(
                    labels=[job_id, 'BUILDING', str(last_build['number']), str(last_build['estimatedDuration']),
                            str(last_build['duration']), last_build["displayName"], last_build['fullDisplayName']],
                    value=(current_milli_time() - last_build['timestamp']) / last_build['estimatedDuration'] * 100
                )

    list_metrics.append(metric)
    return list_metrics
