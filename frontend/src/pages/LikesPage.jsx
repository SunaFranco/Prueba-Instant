import React, { useState, useEffect } from 'react';
import { likesApi } from '../services/api';
import { MovieCard } from '../components/MovieCard';
import { Heart, Loader2, Film, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const LikesPage = () => {
  const [likes, setLikes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingRemoveId, setLoadingRemoveId] = useState(null);

  const fetchLikes = async () => {
    setLoading(true);
    try {
      const res = await likesApi.getLikes();
      setLikes(res.data.likes || []);
    } catch (err) {
      console.error('Error al cargar likes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLikes();
  }, []);

  const handleRemoveLike = async (movie) => {
    const tmdbId = movie.tmdb_id;
    setLoadingRemoveId(tmdbId);
    try {
      await likesApi.removeLike(tmdbId);
      setLikes((prev) => prev.filter((item) => item.tmdb_id !== tmdbId));
    } catch (err) {
      console.error('Error al remover like:', err);
    } finally {
      setLoadingRemoveId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-rose-500/10 rounded-xl text-rose-400 border border-rose-500/20">
              <Heart className="w-5 h-5 fill-rose-500" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Mis Películas Favoritas
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Tienes <span className="text-slate-200 font-semibold">{likes.length}</span> películas marcadas con 'Me Gusta'.
          </p>
        </div>

        {likes.length > 0 && (
          <Link
            to="/recommendations"
            className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/20 text-sm transition-all"
          >
            <Sparkles className="w-4 h-4 fill-slate-950" />
            <span>Generar Recomendación</span>
          </Link>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="min-h-[400px] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-rose-400 animate-spin" />
        </div>
      ) : likes.length === 0 ? (
        <div className="text-center py-20 bg-slate-900/40 rounded-2xl border border-slate-800 max-w-lg mx-auto p-8">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-4">
            <Film className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Aún no has agregado favoritas</h3>
          <p className="text-slate-400 text-sm mb-6">
            Explora el catálogo de películas y marca con 'Me gusta' tus favoritas para que la IA aprenda tus gustos.
          </p>
          <Link
            to="/"
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-white font-semibold rounded-xl text-sm transition-colors"
          >
            <Film className="w-4 h-4" />
            <span>Ir al Catálogo</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
          {likes.map((movie) => (
            <MovieCard
              key={movie.tmdb_id}
              movie={movie}
              isLiked={true}
              onToggleLike={handleRemoveLike}
              loadingLike={loadingRemoveId === movie.tmdb_id}
            />
          ))}
        </div>
      )}
    </div>
  );
};
