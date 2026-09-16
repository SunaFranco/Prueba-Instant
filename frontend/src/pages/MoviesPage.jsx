import React, { useState, useEffect } from 'react';
import { moviesApi, likesApi } from '../services/api';
import { MovieCard } from '../components/MovieCard';
import { Search, ChevronLeft, ChevronRight, Loader2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const MoviesPage = () => {
  const [movies, setMovies] = useState([]);
  const [likesMap, setLikesMap] = useState({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingLikeId, setLoadingLikeId] = useState(null);

  // Cargar lista de likes del usuario para sincronizar el estado visual del botón
  const fetchUserLikes = async () => {
    try {
      const res = await likesApi.getLikes();
      const map = {};
      (res.data.likes || []).forEach((like) => {
        map[like.tmdb_id] = true;
      });
      setLikesMap(map);
    } catch (err) {
      console.error('Error al cargar likes del usuario:', err);
    }
  };

  // Cargar películas desde la API (TMDB)
  const fetchMovies = async () => {
    setLoading(true);
    try {
      const res = await moviesApi.getMovies(page, submittedQuery);
      setMovies(res.data.results || []);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      console.error('Error al cargar películas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserLikes();
  }, []);

  useEffect(() => {
    fetchMovies();
  }, [page, submittedQuery]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    setSubmittedQuery(searchQuery.trim());
  };

  const handleToggleLike = async (movie) => {
    const tmdbId = movie.tmdb_id;
    const isCurrentlyLiked = !!likesMap[tmdbId];
    setLoadingLikeId(tmdbId);

    try {
      if (isCurrentlyLiked) {
        await likesApi.removeLike(tmdbId);
        setLikesMap((prev) => {
          const updated = { ...prev };
          delete updated[tmdbId];
          return updated;
        });
      } else {
        await likesApi.addLike(tmdbId, {
          title: movie.title,
          overview: movie.overview,
          poster_path: movie.poster_path,
          release_date: movie.release_date,
          genres: movie.genres,
          vote_average: movie.vote_average
        });
        setLikesMap((prev) => ({ ...prev, [tmdbId]: true }));
      }
    } catch (err) {
      console.error('Error al actualizar like:', err);
    } finally {
      setLoadingLikeId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Explora el Catálogo de Películas
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Marca las películas que te gustaron para entrenar el motor de recomendación inteligente.
          </p>
        </div>
        <Link
          to="/recommendations"
          className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-amber-500/20 text-sm transition-all shrink-0"
        >
          <Sparkles className="w-4 h-4 fill-slate-950" />
          <span>Pedir Recomendación AI</span>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 max-w-xl">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar por título (ej. Inception, Matrix, Dune)..."
              className="w-full pl-11 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl text-sm border border-slate-700 transition-colors"
          >
            Buscar
          </button>
        </form>
      </div>

      {/* Movies Grid */}
      {loading ? (
        <div className="min-h-[400px] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
        </div>
      ) : movies.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/40 rounded-2xl border border-slate-800">
          <p className="text-slate-400 text-sm">No se encontraron películas para los criterios de búsqueda.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
          {movies.map((movie) => (
            <MovieCard
              key={movie.tmdb_id}
              movie={movie}
              isLiked={!!likesMap[movie.tmdb_id]}
              onToggleLike={handleToggleLike}
              loadingLike={loadingLikeId === movie.tmdb_id}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && movies.length > 0 && (
        <div className="flex items-center justify-center gap-4 mt-12">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="flex items-center space-x-1.5 px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Anterior</span>
          </button>
          <span className="text-xs font-semibold text-slate-400">
            Página <span className="text-slate-100">{page}</span> de <span className="text-slate-100">{totalPages}</span>
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="flex items-center space-x-1.5 px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-slate-900 transition-colors"
          >
            <span>Siguiente</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
