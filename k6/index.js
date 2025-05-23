import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

const vusCount = 500;
const candidatesCount = 10;
const gradesCount = 7;
const url = __ENV["HOSTNAME"] || "http://localhost:8000";

export const options = {
    stages: [
        { duration: '30s', target: vusCount },
        { duration: '30s', target: vusCount },
        { duration: '30s', target: 0 },
    ],
}

export async function setup() {
    const isResticted = true;
    const votersCount = isResticted ? vusCount : 0;

    const election = {
        name: "Test",
        hide_results: true,
        restricted: isResticted,
        grades: [],
        num_voters: votersCount,
        candidates: []
    }
    
    for (let i = 0; i < candidatesCount; ++i) {
        election.candidates.push({
            name: `Candidate ${i}`,
            description: "",
            image: ""
        });
    }

    for (let i = 0; i < gradesCount; ++i) {
        election.grades.push({
            name: `Grade ${i}`,
            value: i,
        });
    }

    const payload = await http.post(`${url}/elections`, JSON.stringify(election), {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    });

    if (payload.status < 200 || payload.status >= 300) {
        throw new Error(`Error creating election: ${payload}`);
    }

    const result = JSON.parse(payload.body);

    if ("details" in result)
        throw new Error(`Error creating election: ${payload.details}`);

    return result;
}

export default async function (data) {
    const index = exec.vu.idInTest-1;
    const token = data.invites != null && data.invites.length > 0 ? data.invites[index] : undefined;

    const electionPayload = await http.get(`${url}/elections/${data.ref}`);

    check(electionPayload, {
        'GET elections returns status 200': (r) => r.status === 200,
    });

    if (electionPayload.status < 200 || electionPayload.status >= 300) {
        console.log("Fail to get election");
        sleep(7);
        return;
    }

    const election = JSON.parse(electionPayload.body);

    // previous ballots is requested to identify if user already voted (context of a restricted election)
    if (token != undefined) {
        const ballotsPayload = await http.get(`${url}/ballots`, {
            headers: {
                "Authorization":`Bearer ${token}`,
                'Accept': 'application/json',
            }
        });

        // first time = should be empty = 404
        const expectedState = exec.vu.iterationInInstance === 0 ? 404 : 200;

        check(ballotsPayload, {
            'GET ballots returns status 200': (r) => r.status === expectedState,
        });
    }

    sleep(7);

    const grades = election.grades;
    const candidates = election.candidates;
    const votes = [];

    for (let i = 0; i < candidates.length; ++i) {
        votes.push({
            candidate_id: candidates[i].id,
            grade_id: grades[Math.floor(Math.random() * grades.length)].id,
        });
    }

    if (token != null) {
        const ballotsPayload = await http.put(`${url}/ballots`, JSON.stringify({
            votes: votes
        }), {
            headers: {
                "Authorization":`Bearer ${token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        });

        if (ballotsPayload.status != 200)
            console.log(ballotsPayload.body);

        check(ballotsPayload, {
            'PUT ballots returns status 200': (r) => r.status === 200,
        });
    } 
    else {
        const ballotsPayload = http.post(`${url}/ballots`, JSON.stringify({
            votes: votes,
            election_ref: election.ref
        }), {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        });

        check(ballotsPayload, {
            'POST ballots returns status 200': (r) => r.status === 200,
        });
    }

    sleep(10);
}