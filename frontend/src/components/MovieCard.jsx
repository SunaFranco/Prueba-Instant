import React from 'react';
import { Heart, Star, Calendar } from 'lucide-react';

export const MovieCard = ({ movie, isLiked, onToggleLike, loadingLike }) => {
  const { tmdb_id, title, overview, poster_path, release_date, genres, vote_average } = movie;

  return (
    <div className="group bg-slate-900/60 rounded-xl overflow-hidden border border-slate-800 hover:border-slate-700 shadow-md hover:shadow-xl hover:shadow-sky-500/5 transition-all flex flex-col">
      {/* Poster Image */}
      <div className="relative aspect-[2/3] w-full bg-slate-800 overflow-hidden">
        {poster_path ? (
          <img
            src={poster_path}
            alt={title}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-slate-800 text-slate-500 text-sm">
            Sin Póster
          </div>
        )}

        {/* Rating Badge */}
        {vote_average > 0 && (
          <div className="absolute top-2.5 left-2.5 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md border border-slate-700/50 flex items-center space-x-1">
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span className="text-xs font-bold text-slate-200">{vote_average}</span>
          </div>
        )}

        {/* Like Button */}
        {onToggleLike && (
          <button
            onClick={() => onToggleLike(movie)}
            disabled={loadingLike}
            title={isLiked ? "Quitar de favoritos" : "Marcar como Me Gusta"}
            className={`absolute top-2.5 right-2.5 p-2 rounded-full backdrop-blur-md transition-all ${
              isLiked
                ? 'bg-rose-500/90 text-white shadow-lg shadow-rose-500/30 scale-105'
                : 'bg-slate-950/70 text-slate-300 hover:text-rose-400 hover:bg-slate-900 border border-slate-700/50'
            }`}
          >
            <Heart className={`w-4 h-4 ${isLiked ? 'fill-white' : ''}`} />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <h3 className="font-semibold text-base text-slate-100 line-clamp-1 group-hover:text-sky-400 transition-colors">
              {title}
            </h3>
          </div>

          {/* Release Date */}
          {release_date && (
            <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-2.5">
              <Calendar className="w-3.5 h-3.5" />
              <span>{release_date.slice(0, 4)}</span>
            </div>
          )}

          {/* Overview */}
          <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-3">
            {overview || 'Sin descripción disponible.'}
          </p>
        </div>

        {/* Genres */}
        {genres && genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-auto pt-2">
            {genres.slice(0, 3).map((genre, idx) => (
              <span
                key={idx}
                className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/50"
              >
                {genre}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
