import React, { useState, useEffect, useRef } from 'react';
import { recommendationsApi, likesApi } from '../services/api';
import { Sparkles, Loader2, Calendar, Star, AlertCircle, RefreshCw, CheckCircle2, Heart } from 'lucide-react';

export const RecommendationsPage = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [activeJob, setActiveJob] = useState(null); // { jobId, status, result, error }
  const [savingFavId, setSavingFavId] = useState(null);
  const pollIntervalRef = useRef(null);

  // Cargar historial de recomendaciones previas
  const fetchRecommendations = async () => {
    setLoadingList(true);
    try {
      const res = await recommendationsApi.getRecommendations();
      setRecommendations(res.data.recommendations || []);
    } catch (err) {
      console.error('Error al cargar recomendaciones:', err);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Agregar a favoritos y remover del historial / vista activa
  const handleAddToFavorites = async (rec) => {
    if (!rec || savingFavId) return;
    setSavingFavId(rec.id);
    try {
      const tmdbId = rec.recommended_tmdb_id || 0;
      await likesApi.addLike(tmdbId, {
        title: rec.recommended_title,
        overview: rec.overview,
        poster_path: rec.poster_path,
        release_date: rec.release_date,
        genres: rec.genres,
        vote_average: rec.vote_average,
      });

      // Eliminar de Supabase / backend
      await recommendationsApi.deleteRecommendation(rec.id);

      // Remover inmediatamente del estado local de la lista
      setRecommendations((prev) => prev.filter((r) => r.id !== rec.id));

      // Remover de la tarjeta activa si está presente
      setActiveJob((prev) => {
        if (!prev || !prev.results) return prev;
        return {
          ...prev,
          results: prev.results.filter((r) => r.id !== rec.id)
        };
      });
    } catch (err) {
      console.error('Error al agregar a favoritos desde historial:', err);
    } finally {
      setSavingFavId(null);
    }
  };

  // Polling del estado del trabajo en segundo plano
  const startPolling = (jobId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await recommendationsApi.getStatus(jobId);
        const { status, recommendations: recsList, recommendation, error_message } = res.data;

        if (status === 'COMPLETED') {
          clearInterval(pollIntervalRef.current);
          const finalResults = (recsList && recsList.length > 0) ? recsList : (recommendation ? [recommendation] : []);
          setActiveJob({ jobId, status: 'COMPLETED', results: finalResults });
          setRequesting(false);
          fetchRecommendations(); // Refrescar el historial
        } else if (status === 'FAILED') {
          clearInterval(pollIntervalRef.current);
          setActiveJob({ jobId, status: 'FAILED', error: error_message || 'Fallo en la inferencia del modelo.' });
          setRequesting(false);
        } else {
          setActiveJob((prev) => ({ ...prev, status }));
        }
      } catch (err) {
        console.error('Error durante polling de recomendación:', err);
      }
    }, 2000);
  };

  const handleRequestRecommendation = async () => {
    setRequesting(true);
    setActiveJob({ jobId: null, status: 'PENDING', results: [], error: null });

    try {
      const res = await recommendationsApi.requestRecommendation();
      const { job_id } = res.data;
      setActiveJob({ jobId: job_id, status: 'PENDING', results: [], error: null });
      startPolling(job_id);
    } catch (err) {
      console.error('Error al encolar recomendación:', err);
      setActiveJob({
        jobId: null,
        status: 'FAILED',
        error: err.response?.data?.error || 'No se pudo iniciar la solicitud.'
      });
      setRequesting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header & CTA */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-8 p-6 sm:p-8 bg-gradient-to-r from-amber-500/10 via-slate-900 to-slate-900 rounded-3xl border border-amber-500/20 shadow-xl shadow-amber-500/5">
        <div>
          <div className="flex items-center space-x-2.5 mb-2">
            <div className="p-2.5 bg-amber-500/20 rounded-2xl text-amber-400 border border-amber-500/30">
              <Sparkles className="w-6 h-6 fill-amber-400" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Motor de Recomendación AI
            </h1>
          </div>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            Nuestro sistema analiza tus películas favoritas, consulta a Groq solicitando 10 candidatas, deduplica contra tu historial previo y te entrega las 3 mejores recomendaciones personalizadas.
          </p>
        </div>

        <button
          onClick={handleRequestRecommendation}
          disabled={requesting}
          className="flex items-center space-x-2.5 px-6 py-3.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-extrabold rounded-2xl shadow-xl shadow-amber-500/20 text-sm transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50 shrink-0"
        >
          {requesting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Procesando en cola...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 fill-slate-950" />
              <span>Solicitar Nueva Recomendación</span>
            </>
          )}
        </button>
      </div>

      {/* Active Processing Card */}
      {activeJob && (
        <div className="mb-10">
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-2xl backdrop-blur-md">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center space-x-2">
              <span>Estado del Trabajo</span>
              <span className="text-slate-600">•</span>
              <span className="text-sky-400 font-mono text-[11px]">{activeJob.jobId || 'Iniciando'}</span>
            </h2>

            {activeJob.status === 'PENDING' && (
              <div className="flex items-center space-x-3 text-amber-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm font-medium">En cola de Redis. Esperando turno del worker de Groq...</span>
              </div>
            )}

            {activeJob.status === 'PROCESSING' && (
              <div className="flex items-center space-x-3 text-sky-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm font-medium">Worker analizando 10 candidatas en Groq y deduplicando contra tu historial...</span>
              </div>
            )}

            {activeJob.status === 'FAILED' && (
              <div className="flex items-center space-x-3 text-rose-400">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span className="text-sm">{activeJob.error}</span>
              </div>
            )}

            {activeJob.status === 'COMPLETED' && activeJob.results && activeJob.results.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-emerald-400 text-sm font-semibold">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>¡{activeJob.results.length} recomendaciones listas y deduplicadas!</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
                  {activeJob.results.map((item) => (
                    <div
                      key={item.id || item.recommended_title}
                      className="flex flex-col bg-slate-950/60 p-5 rounded-2xl border border-slate-800/80 shadow-md justify-between"
                    >
                      <div>
                        {item.poster_path ? (
                          <img
                            src={item.poster_path}
                            alt={item.recommended_title}
                            className="w-full h-48 sm:h-56 rounded-xl object-cover shadow-lg mb-4"
                          />
                        ) : (
                          <div className="w-full h-48 sm:h-56 rounded-xl bg-slate-800 flex items-center justify-center text-xs text-slate-500 mb-4">
                            Sin Póster
                          </div>
                        )}

                        <h3 className="text-lg font-bold text-white mb-1.5 line-clamp-1">
                          {item.recommended_title}
                        </h3>

                        <div className="bg-amber-500/10 border border-amber-500/20 p-3.5 rounded-xl text-amber-200/90 text-xs leading-relaxed mb-3">
                          <p className="font-semibold text-amber-400 text-[10px] uppercase tracking-wider mb-1">
                            ¿Por qué te la recomendamos?
                          </p>
                          {item.rationale}
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-3 border-t border-slate-800/50 mt-auto">
                        <button
                          onClick={() => handleAddToFavorites(item)}
                          disabled={savingFavId === item.id}
                          className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white border border-rose-500/20 hover:border-rose-500 rounded-xl text-xs font-semibold transition-all duration-200 active:scale-95 disabled:opacity-50 cursor-pointer"
                          title="Agregar a favoritos y remover de recomendaciones"
                        >
                          {savingFavId === item.id ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              <span>Guardando...</span>
                            </>
                          ) : (
                            <>
                              <Heart className="w-3.5 h-3.5 fill-rose-500/20" />
                              <span>Agregar a Favoritos</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recommendations History */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
          <span>Historial de Recomendaciones</span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            {recommendations.length}
          </span>
        </h2>

        {loadingList ? (
          <div className="min-h-[200px] flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-16 bg-slate-900/40 rounded-2xl border border-slate-800">
            <p className="text-slate-400 text-sm">Aún no has solicitado recomendaciones.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 flex flex-col sm:flex-row gap-4 hover:border-slate-700 transition-all shadow-md"
              >
                {rec.poster_path ? (
                  <img
                    src={rec.poster_path}
                    alt={rec.recommended_title}
                    className="w-24 sm:w-28 rounded-lg object-cover aspect-[2/3] shrink-0 bg-slate-800"
                  />
                ) : (
                  <div className="w-24 sm:w-28 rounded-lg bg-slate-800 flex items-center justify-center text-[10px] text-slate-500 shrink-0 aspect-[2/3]">
                    Sin Póster
                  </div>
                )}

                <div className="flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-base text-slate-100 mb-1">
                      {rec.recommended_title}
                    </h3>
                    <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 mb-2">
                      <p className="text-xs text-amber-300/90 leading-relaxed">
                        {rec.rationale}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500 pt-3 border-t border-slate-800/50 mt-auto">
                    <div className="flex items-center space-x-3">
                      <span>{rec.created_at?.slice(0, 10)}</span>
                      {rec.vote_average > 0 && (
                        <span className="flex items-center space-x-1 text-amber-400 font-bold">
                          <Star className="w-3 h-3 fill-amber-400" />
                          <span>{rec.vote_average}</span>
                        </span>
                      )}
                    </div>

                    <button
                      onClick={() => handleAddToFavorites(rec)}
                      disabled={savingFavId === rec.id}
                      className="flex items-center space-x-1.5 px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white border border-rose-500/20 hover:border-rose-500 rounded-xl text-xs font-semibold transition-all duration-200 active:scale-95 disabled:opacity-50 ml-auto shadow-sm cursor-pointer"
                      title="Agregar a favoritos y remover de recomendaciones"
                    >
                      {savingFavId === rec.id ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Guardando...</span>
                        </>
                      ) : (
                        <>
                          <Heart className="w-3.5 h-3.5 fill-rose-500/20" />
                          <span>Agregar a Favoritos</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
