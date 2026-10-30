// Mirrors the backend response models (backend/app/schemas.py, branch backend-prot).

/** ISO weekday numbering, Monday = 1. */
export type Weekday = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export const WORK_WEEK: Weekday[] = [1, 2, 3, 4, 5];

export const WEEKDAY_LABELS: Record<Weekday, string> = {
    1: 'Poniedziałek',
    2: 'Wtorek',
    3: 'Środa',
    4: 'Czwartek',
    5: 'Piątek',
    6: 'Sobota',
    7: 'Niedziela',
};

/** 'plain' – data parsed from the official site; 'annotated' – plus notes left by users. */
export type ViewMode = 'plain' | 'annotated';

export interface SourceInfo {
    version: string;
    fetched_at: string;
}

// --- GET /api/v1/catalog ---

export interface CatalogGroup {
    id: string;
    label: string;
}

export interface CatalogElective {
    id: string;
    name: string;
    groups: CatalogGroup[];
}

export interface CatalogProgram {
    id: string;
    name: string;
    groups: CatalogGroup[];
    electives: CatalogElective[];
}

export interface CatalogResponse {
    schema_version: number;
    source: SourceInfo;
    programs: CatalogProgram[];
}

// --- GET /api/v1/schedule ---

export interface Ref {
    id: string;
    name: string;
}

export interface ItemGroup {
    id: string | null;
    label: string | null;
    program_wide: boolean;
}

export interface Block {
    weekday: Weekday;
    start_hour: number;
    count: number;
}

export interface Effective {
    weekday: Weekday;
    start_time: string; // HH:MM
    end_time: string; // HH:MM
    mode: string; // 'stationary' | 'remote' | ...
    date_from: string | null; // ISO date
    date_to: string | null; // ISO date
}

export interface Remark {
    raw: string | null;
    parse_status: string; // 'ok' | 'partial' | ...
    unparsed: string | null;
    needs_review: boolean;
}

/** User-submitted correction; shape is not defined by the backend yet. */
export type Proposal = Record<string, unknown>;

export interface ScheduleItem {
    id: string;
    course: Ref;
    type: string | null; // 'wykład' | 'laboratorium' | 'ćwiczenia' | ...
    group: ItemGroup | null;
    teachers: Ref[];
    room: string | null;
    block: Block;
    effective: Effective;
    patched_fields: string[];
    remark: Remark;
    proposals: Proposal[];
}

export interface ScheduleResponse {
    schema_version: number;
    program: Ref;
    source: SourceInfo & { timezone: string };
    items: ScheduleItem[];
}
