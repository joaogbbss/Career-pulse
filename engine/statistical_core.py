import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler


class CareerStatisticalEngine:
    """
    Motor Estatístico de 6 Camadas para Curvas de Carreira no Futebol:
    1. Encolhimento Bayesiano Empírico (Empirical Bayes Shrinkage) + PAdj (Ajuste de Posse) + Força da Liga (Elo)
    2. Ortogonalização de Pilares (Finalização, Criação/Progressão, Retenção, Defesa)
    3. Clusterização Tática Dinâmica via Gaussian Mixture Models (GMM)
    4. Modelo de Espaço de Estados: Filtro de Kalman + Rauch-Tung-Striebel (RTS) Smoother
    5. Quebra Estrutural de Lesões e Projeção Contrafactual (Delta Aging Curve)
    6. Índice de Glória e Decisão (WPA & Match Importance Multiplier)
    """

    def __init__(self, m0_minutes: float = 630.0, ref_elo: float = 1800.0, elo_gamma: float = 0.85):
        self.m0_minutes = m0_minutes  # Equivalente a 7 partidas completas de 90 min para estabilizar a priori
        self.ref_elo = ref_elo
        self.elo_gamma = elo_gamma

    # =========================================================================
    # CAMADA 1: PRÉ-PROCESSAMENTO, BAYESIAN SHRINKAGE, PADJ E FORÇA DA LIGA
    # =========================================================================
    def empirical_bayes_shrinkage(self, raw_rate: pd.Series, minutes: pd.Series, prior_mean: float) -> pd.Series:
        """Encolhe taxas de poucos minutos em direção à média da posição para eliminar explosões de variância."""
        weight = minutes / (minutes + self.m0_minutes)
        return weight * raw_rate + (1.0 - weight) * prior_mean

    @staticmethod
    def possession_adjust(defensive_actions: pd.Series, team_possession_pct: pd.Series, k: float = 6.0) -> pd.Series:
        """Normaliza ações defensivas via função sigmoide PAdj (padrão StatsBomb) para posse neutra (50%)."""
        poss_ratio = team_possession_pct / 100.0
        multiplier = 2.0 / (1.0 + np.exp(-k * (poss_ratio - 0.5)))
        return defensive_actions * multiplier

    def league_strength_multiplier(self, opponent_elo: pd.Series) -> pd.Series:
        """Calcula o fator de força da liga/adversário (Lambda_t) com base no ClubElo/Opta Rating."""
        return (opponent_elo / self.ref_elo) ** self.elo_gamma

    # =========================================================================
    # CAMADA 2 & 3: PILARES ORTOGONAIS E CLUSTERIZAÇÃO TÁTICA GMM
    # =========================================================================
    def compute_orthogonal_pillars(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma estatísticas brutas por jogo nos 4 Pilares Ortogonais ajustados por minutos, posse e Bayes.
        Espera colunas: minutes, npxG, goals, xAG, sca, prog_passes, prog_carries, pass_comp_pct,
                        tackles, interceptions, blocks, aerials_won, team_poss, opp_elo
        """
        df = df.copy()
        min_90 = np.maximum(df["minutes"] / 90.0, 0.05)

        # Taxas brutas por 90 min
        finishing_raw = (df["npxG"] + 0.35 * (df["goals"] - df["npxG"])) / min_90
        creation_raw = (df["xAG"] * 2.2 + df["sca"] * 0.25 + (df["prog_passes"] + df["prog_carries"]) * 0.08) / min_90
        retention_raw = (df["pass_comp_pct"] - 75.0) * 0.1 + (df["prog_passes"] / min_90) * 0.05

        def_raw_counts = df["tackles"] + df["interceptions"] + df["blocks"] * 0.8 + df["aerials_won"] * 0.5
        def_padj = self.possession_adjust(def_raw_counts, df["team_poss"]) / min_90

        # Encolhimento Bayesiano por pilar
        df["pillar_finishing"] = self.empirical_bayes_shrinkage(finishing_raw, df["minutes"], finishing_raw.median())
        df["pillar_creation"] = self.empirical_bayes_shrinkage(creation_raw, df["minutes"], creation_raw.median())
        df["pillar_retention"] = self.empirical_bayes_shrinkage(retention_raw, df["minutes"], retention_raw.median())
        df["pillar_defense"] = self.empirical_bayes_shrinkage(def_padj, df["minutes"], def_padj.median())

        # Normalização robusta (Z-Score resistente a outliers)
        pillar_cols = ["pillar_finishing", "pillar_creation", "pillar_retention", "pillar_defense"]
        scaler = RobustScaler()
        z_pillars = pd.DataFrame(
            scaler.fit_transform(df[pillar_cols]),
            columns=[f"z_{c}" for c in pillar_cols],
            index=df.index
        )
        df = pd.concat([df, z_pillars], axis=1)

        # Clusterização Tática Suave (GMM) para ponderar arquétipos dinamicamente
        n_clusters = min(3, max(1, len(df) // 15))
        gmm = GaussianMixture(n_components=n_clusters, covariance_type="full", random_state=42)
        gmm.fit(z_pillars)
        probs = gmm.predict_proba(z_pillars)

        # Pesos adaptativos: cada arquétipo valoriza mais os pilares onde tem centroide superior
        means = gmm.means_
        positive_weights = np.exp(means) / np.sum(np.exp(means), axis=1, keepdims=True)
        dynamic_weights = probs @ positive_weights  # (N_jogos, 4)

        raw_z_composite = np.sum(z_pillars.values * dynamic_weights, axis=1)
        lambda_elo = self.league_strength_multiplier(df["opp_elo"])

        df["z_composite_adjusted"] = raw_z_composite * lambda_elo
        return df

    # =========================================================================
    # CAMADA 4: FILTRO DE KALMAN + RAUCH-TUNG-STRIEBEL (RTS) SMOOTHER
    # =========================================================================
    @staticmethod
    def kalman_rts_smoother(
        observations: np.ndarray,
        minutes: np.ndarray,
        days_gap: np.ndarray,
        injury_flags: np.ndarray,
        base_obs_var: float = 0.65,
        base_process_var: float = 0.018
    ):
        """
        Executa o Filtro de Kalman Forward e o RTS Smoother Backward para extrair:
        - theta_smooth: A verdadeira fase técnica latente sem lag temporal
        - var_smooth: A incerteza (variância a posteriori) para desenhar a aura do gráfico
        """
        n = len(observations)
        theta_pred = np.zeros(n)
        var_pred = np.zeros(n)
        theta_filt = np.zeros(n)
        var_filt = np.zeros(n)

        # Inicialização no primeiro ponto
        theta_filt[0] = observations[0]
        var_filt[0] = base_obs_var

        # Passo 1: Forward Pass (Filtro de Kalman)
        for t in range(1, n):
            # Variância de transição cresce com o hiato de dias entre partidas (férias/lesões aumentam incerteza)
            dt_factor = max(1.0, days_gap[t] / 7.0)
            q_t = base_process_var * dt_factor

            # Quebra estrutural de lesão no estado a priori
            injury_decay = 0.88 if injury_flags[t] > 0 else 1.0

            theta_pred[t] = theta_filt[t - 1] * injury_decay
            var_pred[t] = (var_filt[t - 1] * (injury_decay ** 2)) + q_t

            # Variância da observação inversamente proporcional aos minutos jogados na partida
            min_ratio = max(0.1, minutes[t] / 90.0)
            r_t = base_obs_var / min_ratio

            # Ganho de Kalman
            k_gain = var_pred[t] / (var_pred[t] + r_t)
            theta_filt[t] = theta_pred[t] + k_gain * (observations[t] - theta_pred[t])
            var_filt[t] = (1.0 - k_gain) * var_pred[t]

        # Passo 2: Backward Pass (Rauch-Tung-Striebel Smoother - elimina o lag de fase)
        theta_smooth = np.zeros(n)
        var_smooth = np.zeros(n)
        theta_smooth[-1] = theta_filt[-1]
        var_smooth[-1] = var_filt[-1]

        for t in range(n - 2, -1, -1):
            injury_decay = 0.88 if injury_flags[t + 1] > 0 else 1.0
            c_gain = (var_filt[t] * injury_decay) / max(var_pred[t + 1], 1e-8)
            theta_smooth[t] = theta_filt[t] + c_gain * (theta_smooth[t + 1] - theta_pred[t + 1])
            var_smooth[t] = var_filt[t] + (c_gain ** 2) * (var_smooth[t + 1] - var_pred[t + 1])

        return theta_smooth, var_smooth

    # =========================================================================
    # CAMADA 5: CURVA CONTRAFACTUAL PÓS-LESÃO (E SE NÃO TIVESSE MACHUCADO?)
    # =========================================================================
    @staticmethod
    def compute_counterfactual_trajectory(df: pd.DataFrame, score_col: str = "career_index") -> pd.Series:
        """
        Projeta a curva fantasma ('E se?') caso o atleta não tivesse sofrido lesões graves (>30 dias),
        combinando o pico pré-lesão com uma curva fisiológica parabólica de envelhecimento (pico aos 26.5 anos).
        """
        ages = df["age"].values
        scores = df[score_col].values
        severe_injuries = df["injury_days_missed"].values >= 30

        counterfactual = np.copy(scores)
        in_counterfactual_regime = False
        anchor_score = 0.0
        anchor_age = 25.0

        def aging_curve_delta(age_now, age_ref, peak_age=26.5):
            # Derivada integrada de uma curva parabólica de performance física/técnica por idade
            return -0.32 * ((age_now - peak_age) ** 2 - (age_ref - peak_age) ** 2)

        for t in range(len(df)):
            if severe_injuries[t] and not in_counterfactual_regime:
                in_counterfactual_regime = True
                # Pega a média recente antes da lesão como âncora
                window_start = max(0, t - 5)
                anchor_score = np.max(scores[window_start:t+1])
                anchor_age = ages[t]

            if in_counterfactual_regime:
                projected = anchor_score + aging_curve_delta(ages[t], anchor_age)
                # Só mantém a linha fantasma acima da real quando a lesão de fato derrubou o patamar do atleta
                counterfactual[t] = max(scores[t], min(99.0, projected))

        return pd.Series(counterfactual, index=df.index).ewm(span=6).mean()

    # =========================================================================
    # CAMADA 6: ÍNDICE DE GLÓRIA E DECISÃO (CLUTCH & LEGACY GLOW)
    # =========================================================================
    @staticmethod
    def compute_glory_and_tier(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula o Índice Técnico (0-100), as bandas de confiança e o Índice de Glória/Decisão (Glow).
        """
        df = df.copy()
        # Converte o estado latente suavizado em percentil 0-100 calibrado (escala de elite)
        z_mean = df["theta_smooth"].mean()
        z_std = max(df["theta_smooth"].std(), 0.35)
        standardized = (df["theta_smooth"] - z_mean) / z_std

        # Escala logística/normal mapeada para 0-100 (média de carreira = ~65, auge = 90-98, baixa = 25-45)
        df["career_index"] = np.clip(norm.cdf(standardized * 0.85 + 0.35) * 100.0, 12.0, 99.4).round(1)

        # Bandas de incerteza (Aura do Filtro de Kalman)
        uncertainty_pts = np.clip(np.sqrt(df["var_smooth"]) * 18.0, 2.0, 16.0)
        df["ci_lower"] = np.clip(df["career_index"] - uncertainty_pts, 5.0, 99.0).round(1)
        df["ci_upper"] = np.clip(df["career_index"] + uncertainty_pts, 5.0, 99.9).round(1)

        # Curva Contrafactual Sem Lesões
        df["counterfactual_index"] = CareerStatisticalEngine.compute_counterfactual_trajectory(df, "career_index").round(1)

        # Glória = Score * Peso do Jogo (Omega) * Win Probability Added (WPA)
        # Omega: 1.0 (Liga), 1.35 (Clássico), 1.8 (Mata-Mata Continental), 3.0 (Final/Título)
        df["glory_glow"] = np.clip(
            df["career_index"] * df["match_importance"] * (1.0 + 0.6 * df["wpa_clutch"]),
            0.0,
            250.0
        ).round(1)

        # Classificação de Fase para Estilização Dinâmica no Front-End
        def assign_phase(row):
            if row["injury_days_missed"] >= 21:
                return "INJURY_VALLEY"
            if row["career_index"] >= 85.0 or row["glory_glow"] >= 155.0:
                return "GOD_MODE"
            if row["career_index"] >= 68.0:
                return "PRIME"
            if row["career_index"] >= 50.0:
                return "REGULAR"
            return "SLUMP"

        df["phase_state"] = df.apply(assign_phase, axis=1)
        return df

    def run_full_pipeline(self, raw_matches_df: pd.DataFrame) -> pd.DataFrame:
        """Executa as 6 camadas sequencialmente sobre o DataFrame cronológico de um jogador."""
        df = raw_matches_df.sort_values("date").reset_index(drop=True)
        df["date_dt"] = pd.to_datetime(df["date"])
        df["days_gap"] = df["date_dt"].diff().dt.days.fillna(7).clip(lower=3, upper=180)

        # Camadas 1, 2 e 3
        df = self.compute_orthogonal_pillars(df)

        # Camada 4 (Kalman + RTS)
        theta_smooth, var_smooth = self.kalman_rts_smoother(
            observations=df["z_composite_adjusted"].values,
            minutes=df["minutes"].values,
            days_gap=df["days_gap"].values,
            injury_flags=(df["injury_days_missed"] > 14).astype(float).values
        )
        df["theta_smooth"] = theta_smooth
        df["var_smooth"] = var_smooth

        # Camadas 5 e 6
        df = self.compute_glory_and_tier(df)
        return df
