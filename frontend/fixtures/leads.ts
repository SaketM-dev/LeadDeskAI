import type { Lead } from '@/types/api';

// Fictional demo records only. Do not treat these as real prospect data.
export const demoLeads: Lead[] = [
  { id: 'demo-1048', full_name: 'Rohan Sharma', source: 'whatsapp', stage: 'qualified', lead_score: 85 },
  { id: 'demo-1047', full_name: 'Priya Patel', source: 'instagram', stage: 'contacted', lead_score: 72 },
  { id: 'demo-1046', full_name: 'Aarav Singh', source: 'website_form', stage: 'new', lead_score: 68 },
  { id: 'demo-1045', full_name: 'Sneha Kulkarni', source: 'walk_in', stage: 'new', lead_score: 54 },
  { id: 'demo-1044', full_name: 'Kabir Deshmukh', source: 'whatsapp', stage: 'demo_booked', lead_score: 91 },
  { id: 'demo-1043', full_name: 'Meera Joshi', source: 'phone_call', stage: 'nurturing', lead_score: 62 },
];
