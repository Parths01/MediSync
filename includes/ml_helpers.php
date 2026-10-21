<?php
/**
 * ml_helpers.php
 *
 * Lightweight, pure-PHP heuristics for the three AI/ML features.
 * No external service required.  Replace individual functions with real
 * model API calls once you have enough real data to train on.
 */

// ---------------------------------------------------------------------------
// 1.  SYMPTOM → SPECIALTY RECOMMENDER
// ---------------------------------------------------------------------------

/**
 * Maps free-text symptoms to a ranked list of medical specialties.
 *
 * Returns an array of ['specialty' => string, 'score' => int, 'matched' => string[]]
 * sorted descending by score.
 */
function ml_recommend_specialties(string $symptomText): array
{
    $text = mb_strtolower($symptomText);

    $map = [
        'Neurologist' => [
            'headache', 'migraine', 'seizure', 'epilepsy', 'numbness',
            'tingling', 'memory loss', 'dizziness', 'vertigo', 'stroke',
            'tremor', 'paralysis', 'neuropathy', 'brain', 'nerve',
            'confusion', 'fainting', 'blackout',
        ],
        'Gynecologist' => [
            'period', 'menstrual', 'pregnancy', 'prenatal', 'ovary',
            'uterus', 'vaginal', 'cervical', 'hormonal', 'fertility',
            'pcos', 'endometriosis', 'discharge', 'pap smear', 'breast',
            'menopause', 'cramp', 'irregular cycle',
        ],
        'Physiotherapy' => [
            'back pain', 'joint pain', 'knee pain', 'shoulder pain',
            'muscle', 'sprain', 'strain', 'fracture', 'rehabilitation',
            'posture', 'stiffness', 'swelling', 'mobility', 'physiotherapy',
            'sports injury', 'arthritis', 'sciatica', 'frozen shoulder',
            'neck pain', 'hip pain',
        ],
        'Cardiologist' => [
            'chest pain', 'heart', 'palpitation', 'shortness of breath',
            'high blood pressure', 'hypertension', 'cholesterol',
            'irregular heartbeat', 'cardiac', 'angina', 'blood pressure',
        ],
        'Dermatologist' => [
            'rash', 'acne', 'skin', 'eczema', 'psoriasis', 'itching',
            'hives', 'mole', 'hair loss', 'nail', 'fungal', 'allergy',
            'wound', 'scar', 'pigmentation',
        ],
        'Gastroenterologist' => [
            'stomach', 'abdominal pain', 'nausea', 'vomiting', 'diarrhea',
            'constipation', 'bloating', 'acid reflux', 'ulcer', 'ibs',
            'liver', 'gallbladder', 'jaundice', 'digestive', 'crohn',
            'colitis', 'indigestion',
        ],
        'Orthopedic' => [
            'bone', 'fracture', 'joint', 'ligament', 'tendon', 'cartilage',
            'scoliosis', 'osteoporosis', 'ankle', 'wrist', 'elbow', 'spine',
        ],
        'ENT' => [
            'ear', 'nose', 'throat', 'hearing loss', 'tinnitus', 'sore throat',
            'sinusitis', 'cold', 'runny nose', 'blocked nose', 'sneezing',
            'tonsil', 'adenoid', 'hoarse',
        ],
        'Ophthalmologist' => [
            'eye', 'vision', 'blurry', 'cataract', 'glaucoma', 'dry eye',
            'eye pain', 'redness in eye', 'conjunctivitis',
        ],
        'Psychiatrist' => [
            'anxiety', 'depression', 'stress', 'panic attack', 'insomnia',
            'sleep disorder', 'mood', 'bipolar', 'schizophrenia', 'ocd',
            'phobia', 'addiction', 'eating disorder', 'mental health',
        ],
        'General Physician' => [
            'fever', 'fatigue', 'weakness', 'weight loss', 'weight gain',
            'cough', 'cold', 'flu', 'infection', 'diabetes', 'thyroid',
            'vitamin', 'routine checkup', 'general',
        ],
    ];

    $results = [];
    foreach ($map as $specialty => $keywords) {
        $matched = [];
        foreach ($keywords as $kw) {
            if (mb_strpos($text, $kw) !== false) {
                $matched[] = $kw;
            }
        }
        if (!empty($matched)) {
            $results[] = [
                'specialty' => $specialty,
                'score'     => count($matched),
                'matched'   => $matched,
            ];
        }
    }

    usort($results, fn($a, $b) => $b['score'] <=> $a['score']);
    return $results;
}


// ---------------------------------------------------------------------------
// 2.  APPOINTMENT NO-SHOW RISK SCORER
// ---------------------------------------------------------------------------

/**
 * Scores a single appointment row for no-show risk.
 *
 * $appt must contain:
 *   appointment_date (datetime string), created_at (datetime string),
 *   past_total (int), past_missed (int)
 *
 * Returns ['risk' => float 0-1, 'label' => 'Low'|'Medium'|'High', 'factors' => string[]]
 */
function ml_noshow_score(array $appt): array
{
    $score   = 0.0;
    $factors = [];

    // Factor 1: lead time (days between booking and appointment)
    $apptTs    = strtotime($appt['appointment_date']);
    $createdTs = strtotime($appt['created_at']);
    $leadDays  = max(0, ($apptTs - $createdTs) / 86400);

    if ($leadDays > 14) {
        $score += 0.25;
        $factors[] = 'Booked far in advance (' . round($leadDays) . ' days)';
    } elseif ($leadDays > 7) {
        $score += 0.10;
        $factors[] = 'Booked ' . round($leadDays) . ' days ahead';
    }

    // Factor 2: appointment hour (early morning / late evening = higher risk)
    $hour = (int) date('G', $apptTs);
    if ($hour < 9 || $hour >= 17) {
        $score += 0.20;
        $factors[] = 'Off-peak time slot (' . date('g:i A', $apptTs) . ')';
    }

    // Factor 3: appointment weekday (Monday, Friday = slightly higher)
    $dow = (int) date('N', $apptTs); // 1=Mon ... 7=Sun
    if ($dow === 1 || $dow === 5) {
        $score += 0.10;
        $factors[] = date('l', $apptTs) . ' appointments have higher skip rates';
    }

    // Factor 4: patient's historical miss rate
    $pastTotal  = (int) ($appt['past_total']  ?? 0);
    $pastMissed = (int) ($appt['past_missed'] ?? 0);
    if ($pastTotal > 0) {
        $missRate = $pastMissed / $pastTotal;
        if ($missRate > 0.5) {
            $score += 0.40;
            $factors[] = 'Patient missed ' . $pastMissed . '/' . $pastTotal . ' past appointments';
        } elseif ($missRate > 0.25) {
            $score += 0.20;
            $factors[] = 'Patient has some missed appointments (' . $pastMissed . '/' . $pastTotal . ')';
        }
    }

    $score = min(1.0, $score);

    if ($score >= 0.55) {
        $label = 'High';
    } elseif ($score >= 0.30) {
        $label = 'Medium';
    } else {
        $label = 'Low';
    }

    return [
        'risk'    => round($score, 2),
        'label'   => $label,
        'factors' => $factors ?: ['No significant risk factors detected'],
    ];
}

/**
 * Suggested action string for a given risk label.
 */
function ml_noshow_action(string $label): string
{
    return match ($label) {
        'High'   => 'Send reminder SMS + consider overbooking slot',
        'Medium' => 'Send a reminder 24 h before',
        default  => 'No special action needed',
    };
}


// ---------------------------------------------------------------------------
// 3.  FEEDBACK SENTIMENT CLASSIFIER
// ---------------------------------------------------------------------------

/**
 * Classifies a single feedback string as 'positive', 'negative', or 'neutral'.
 *
 * Returns ['sentiment' => string, 'score' => int (net positive words minus negative)]
 */
function ml_classify_sentiment(string $text): array
{
    $text = mb_strtolower($text);

    $positive = [
        'excellent', 'great', 'good', 'wonderful', 'amazing', 'fantastic',
        'perfect', 'helpful', 'kind', 'friendly', 'professional', 'satisfied',
        'happy', 'thank', 'thanks', 'appreciate', 'impressed', 'love',
        'best', 'outstanding', 'superb', 'brilliant', 'pleased', 'comfortable',
        'efficient', 'clean', 'prompt', 'attentive', 'caring', 'polite',
        'recommend', 'awesome', 'nice', 'positive', 'well', 'top',
    ];

    $negative = [
        'bad', 'terrible', 'awful', 'poor', 'horrible', 'worst',
        'disappointing', 'rude', 'unprofessional', 'negligent', 'slow',
        'wait', 'long wait', 'careless', 'wrong', 'mistake', 'error',
        'overcharged', 'expensive', 'ignored', 'unhappy', 'unsatisfied',
        'frustrating', 'difficult', 'problem', 'issue', 'complaint',
        'dirty', 'unhygienic', 'late', 'delayed', 'cancelled', 'miss',
        'never', 'not good', 'not helpful', 'not satisfied',
    ];

    $posCount = 0;
    $negCount = 0;

    foreach ($positive as $word) {
        if (mb_strpos($text, $word) !== false) {
            $posCount++;
        }
    }
    foreach ($negative as $word) {
        if (mb_strpos($text, $word) !== false) {
            $negCount++;
        }
    }

    $net = $posCount - $negCount;

    if ($net > 0) {
        $sentiment = 'positive';
    } elseif ($net < 0) {
        $sentiment = 'negative';
    } else {
        $sentiment = 'neutral';
    }

    return ['sentiment' => $sentiment, 'score' => $net];
}
