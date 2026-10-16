import type { LeadDetail } from '@/types/api';

// Fictional records for the UI demo only. No messages or tasks are sent.
const sharedTimeline = (id: string, name: string) => [
  { id: `${id}-e1`, type: 'message' as const, title: 'Enquiry received', description: `${name} asked for course information.`, occurred_at: '2026-10-15T09:20:00Z', channel: 'website_form', actor: 'Prospect' },
  { id: `${id}-e2`, type: 'message' as const, title: 'Counselor replied', description: 'Shared a general overview and asked about learning goals.', occurred_at: '2026-10-15T09:42:00Z', channel: 'whatsapp', actor: 'Admissions counselor' },
  { id: `${id}-e3`, type: 'stage_change' as const, title: 'Lead qualified', description: 'Moved to qualified after expressing interest.', occurred_at: '2026-10-15T10:05:00Z', actor: 'Admissions counselor' },
  { id: `${id}-e4`, type: 'follow_up' as const, title: 'Follow-up suggested', description: 'Confirm approved course schedule before sending specific details.', occurred_at: '2026-10-16T08:30:00Z', actor: 'AI Lead Desk (suggestion only)' },
];

export const demoLeadDetails: Record<string, LeadDetail> = {
  'demo-1048': {
    id: 'demo-1048', full_name: 'Rohan Sharma', source: 'whatsapp', stage: 'qualified', lead_score: 85,
    preferred_language: 'hi', course_interest: 'Data Analytics', phone: '+91 90000 10048',
    email: 'rohan.demo@example.com', assigned_name: 'A. Counselor',
    summary: ['Interested in building practical data analysis skills.', 'Asked about schedule and fees; these facts require approved institute confirmation.', 'Next step: confirm current approved course details and offer a demo slot.'],
    objections: [{ type: 'fees', label: 'Fees', evidence: 'Asked for fee details; no approved fee record is attached.' }, { type: 'time', label: 'Schedule / time', evidence: 'Needs to confirm whether class timings fit his availability.' }],
    next_action: 'Verify the current approved fee and schedule records, then follow up in Hindi.',
    consent: { whatsapp: true, marketing: false }, human_takeover: false,
    timeline: sharedTimeline('demo-1048', 'Rohan Sharma'),
  },
  'demo-1047': {
    id: 'demo-1047', full_name: 'Priya Patel', source: 'instagram', stage: 'contacted', lead_score: 72,
    preferred_language: 'en', course_interest: 'UI/UX Design', assigned_name: 'A. Counselor',
    summary: ['Exploring a career change into design.', 'Asked for a course overview and examples of student work.', 'Next step: share approved curriculum and ask about prior design experience.'],
    objections: [{ type: 'trust', label: 'Trust / proof', evidence: 'Requested examples before deciding.' }],
    next_action: 'Share only approved curriculum and verified portfolio examples.',
    consent: { instagram: true, marketing: false }, human_takeover: false,
    timeline: sharedTimeline('demo-1047', 'Priya Patel'),
  },
  'demo-1046': {
    id: 'demo-1046', full_name: 'Aarav Singh', source: 'website_form', stage: 'new', lead_score: 68,
    preferred_language: 'en', course_interest: 'Full-Stack Development',
    summary: ['Submitted a website enquiry about development training.', 'No confirmed schedule or eligibility details recorded yet.', 'Next step: ask about goals and preferred learning times.'],
    objections: [], next_action: 'Send a consent-checked introductory response and ask one discovery question.',
    consent: { email: true, marketing: false }, human_takeover: false,
    timeline: sharedTimeline('demo-1046', 'Aarav Singh'),
  },
  'demo-1045': {
    id: 'demo-1045', full_name: 'Sneha Kulkarni', source: 'walk_in', stage: 'new', lead_score: 54,
    preferred_language: 'mr', course_interest: 'AI & Machine Learning',
    summary: ['Walk-in enquiry; interests and constraints still need discovery.', 'No course-specific facts have been verified for this record.', 'Next step: capture goals, prior experience and preferred schedule.'],
    objections: [], next_action: 'Complete discovery and confirm consent preferences.',
    consent: { whatsapp: false, marketing: false }, human_takeover: false,
    timeline: sharedTimeline('demo-1045', 'Sneha Kulkarni'),
  },
  'demo-1044': {
    id: 'demo-1044', full_name: 'Kabir Deshmukh', source: 'whatsapp', stage: 'demo_booked', lead_score: 91,
    preferred_language: 'en', course_interest: 'Data Science',
    summary: ['Interested prospect with a demo booking in the demo fixture.', 'Booking is illustrative and has not been confirmed with a calendar provider.', 'Next step: verify provider status before treating the demo as confirmed.'],
    objections: [{ type: 'time', label: 'Availability', evidence: 'Requested a suitable demo time.' }],
    next_action: 'Check the real calendar provider before confirming or changing any booking.',
    consent: { whatsapp: true, marketing: false }, human_takeover: false,
    timeline: sharedTimeline('demo-1044', 'Kabir Deshmukh'),
  },
  'demo-1043': {
    id: 'demo-1043', full_name: 'Meera Joshi', source: 'phone_call', stage: 'nurturing', lead_score: 62,
    preferred_language: 'mr', course_interest: 'Web Development',
    summary: ['Requested more time to compare learning options.', 'No explicit consent for marketing messages is recorded.', 'Next step: use an appropriate counselor-led follow-up only if channel consent permits.'],
    objections: [{ type: 'family_approval', label: 'Family approval', evidence: 'Wants to discuss the decision with family.' }],
    next_action: 'Prepare a counselor note; do not start automated marketing outreach.',
    consent: { phone_call: true, marketing: false }, human_takeover: true,
    timeline: sharedTimeline('demo-1043', 'Meera Joshi'),
  },
};

export function getDemoLeadDetail(leadId: string): LeadDetail | undefined {
  return demoLeadDetails[leadId];
}
