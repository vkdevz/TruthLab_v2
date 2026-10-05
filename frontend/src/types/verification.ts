export type VeracityLabel =
  | 'SUPPORTED'
  | 'CONTRADICTED'
  | 'MISLEADING'
  | 'OUTDATED'
  | 'INSUFFICIENT_EVIDENCE';

export type StanceType = 'SUPPORTS' | 'REFUTES' | 'NEUTRAL';
export type ModalityType = 'TEXT' | 'URL' | 'IMAGE' | 'VIDEO';

export interface AtomicClaim {
  id: string;
  raw_text: string;
  canonical_claim: string;
  checkworthy_score: number;
  is_checkworthy: boolean;
  entities: string[];
  temporal_anchor?: string | null;
  inferred_date?: string | null;
  search_queries: string[];
}

export interface EvidenceSnippet {
  id: string;
  claim_id: string;
  source_name: string;
  source_url: string;
  domain: string;
  domain_credibility_weight: number;
  snippet_text: string;
  publication_date?: string | null;
  retrieval_score: number;
  stance: StanceType;
  stance_probabilities: Record<StanceType, number>;
  is_claim_review: boolean;
  claim_review_rating?: string | null;
}

export interface ImageForensicIndicators {
  has_exif: boolean;
  software_tag?: string | null;
  c2pa_present: boolean;
  ela_max_error: number;
  is_ela_spliced: boolean;
  synthetic_probability: number;
  synthetic_confidence: 'LOW' | 'MODERATE' | 'HIGH';
  forensic_notes: string[];
}

export interface VideoForensicIndicators {
  duration_seconds: number;
  total_frames: number;
  extracted_scenes: number;
  has_audio_track: boolean;
  inconsistent_frame_rate: boolean;
  synthetic_face_probability?: number | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'claim' | 'evidence' | 'source' | 'forensic';
  status?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface EvidenceGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface AuditTrail {
  summary: string;
  supporting_citations: string[];
  refuting_citations: string[];
  temporal_notes: string[];
  media_authenticity_notes: string[];
  limitations: string[];
}

export interface ClaimVerificationResult {
  claim: AtomicClaim;
  veracity: VeracityLabel;
  confidence: number;
  evidence_sufficiency_score: number;
  is_temporal_mismatch: boolean;
  evidence_items: EvidenceSnippet[];
  audit: AuditTrail;
}

export interface FullVerificationResponse {
  job_id: string;
  created_at: string;
  completed_at?: string | null;
  input_modality: ModalityType;
  overall_veracity: VeracityLabel;
  overall_confidence: number;
  claims_verified: ClaimVerificationResult[];
  image_forensics?: ImageForensicIndicators | null;
  video_forensics?: VideoForensicIndicators | null;
  ocr_text?: string | null;
  transcript_text?: string | null;
  evidence_graph: EvidenceGraph;
  executive_summary: string;
  system_limitations: string[];
  uncertainty_level?: 'LOW' | 'MODERATE' | 'HIGH';
  uncertainty_score?: number;
  is_actionable?: boolean;
}

