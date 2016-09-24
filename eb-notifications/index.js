const AWS = require('aws-sdk');
const https = require('https');
const url = require('url');

const region = 'us-east-1';
const elasticbeanstalk = new AWS.ElasticBeanstalk({region: region});

// our minute contains 61 seconds :-/
// just in case to cover potential inconsistencies with running it in intervals
const oneMinute = 61 * 1000;

// Slack stuff
const slackURL = 'https://hooks.slack.com/YOUR_SLACK_URL';

// PagerDuty stuff
const pagerDutyURL = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json';
const pagerDutyServiceKey = 'YOUR_PAGERDUTY_KEY';


function notifyPagerDuty(event, link) {
    console.log(`Notifying PagerDuty`);

    sendRequest(pagerDutyURL, {
        service_key: pagerDutyServiceKey,
        event_type: 'trigger',
        description: `[${event.Severity}] in ${event.EnvironmentName}: ${event.Message}`,
        contexts: [{
            type: 'link',
            text: `Open ${event.EnvironmentName} environment`,
            href: link
        }]
    });
}

function notifySlack(event, link) {
    console.log(`Notifying Slack`);

    const message = `[${event.Severity}] in \<${link}|${event.EnvironmentName}\>: ${event.Message}`;

    sendRequest(slackURL, {
        attachments: [
            {
                fallback: message,
                color: isEventImportant(event) ? 'danger' : 'warning',
                fields: [
                    {
                        title: event.EnvironmentName,
                        value: message,
                        short: false
                    }
                ]
            }
        ]
    });
}

function sendRequest(reqUrl, reqBody) {
    const reqOpts = url.parse(reqUrl);

    reqOpts.method = 'POST';
    reqOpts.headers = {'Content-Type': 'application/json'};

    const req = https.request(reqOpts, function (res) {
        if (res.statusCode !== 200) {
            console.log('failed to send, status code: ' + res.statusCode);
        }
    });

    req.on('error', (e) => {
        console.log('problem with request: ' + e.message);
    });

    req.write(JSON.stringify(reqBody));

    req.end();
}

function generateEnvironmentLink(environment) {
    return `https://console.aws.amazon.com/elasticbeanstalk/home?region=${region}#/environment/dashboard?` +
    `applicationName=${environment.ApplicationName}&environmentId=${environment.EnvironmentId}`;
}

function isEventImportant(event) {
    return event.Severity === 'ERROR' || event.Severity === 'FATAL';
}

function processEvent(event) {
    console.log(`Processing event: ${JSON.stringify(event)}`);

    fetchEnvironment(event.EnvironmentName).then((environment) => {
        const link = generateEnvironmentLink(environment);

        if(isEventImportant(event)) {
            notifyPagerDuty(event, link);
        }

        notifySlack(event, link);
    });
}

function fetchEvents() {
    console.log('Fetching events');

    const params = {
      EndTime: new Date(),
      StartTime: new Date(new Date().getTime() - oneMinute),
      Severity: 'WARN'
    };

    return new Promise((resolve, reject) => {
        elasticbeanstalk.describeEvents(params, (err, data) => {
            if (err) {
                console.log(err, err.stack);
                reject(err);
            } else {
                resolve(data.Events);
            }
        });
    });
}

function fetchEnvironment(name) {
    console.log(`Fetching environment ${name}`);

    const params = {
      EnvironmentNames: [name],
      IncludeDeleted: false
    };

    return new Promise((resolve, reject) => {
        elasticbeanstalk.describeEnvironments(params, (err, data) => {
            if (err) {
                console.log(err, err.stack);
                reject(err);
            } else {
                resolve(data.Environments[0]);
            }
        });
    });
}

exports.handler = (event, context, callback) => {
    fetchEvents().then((events) => {
        events.forEach(event => processEvent(event));
    });
};
