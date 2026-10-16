export type UUID = string;
export type ISOTimestamp = string;
export type Language = 'en' | 'hi' | 'mr' | 'mixed' | string;
export type Channel = 'whatsapp' | 'instagram' | 'phone_call' | 'website_form' | 'email' | 'walk_in' | 'manual' | 'other';
export type LeadStage = 'new' | 'contacted' | 'qualified' | 'demo_booked' | 'demo_attended' | 'nurturing' | 'admitted' | 'lost' | 'do_not_contact';
export interface ApiList<T> { data: T[]; page?: { next_cursor: string | null }; }
export interface ApiErrorBody { error: { code: string; message: string; request_id?: string; details?: unknown[] }; }
