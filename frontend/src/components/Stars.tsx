import { Star } from './Icon'

// Star rating display. Renders an honest "No reviews yet" when there is no data.
export default function Stars({ rating, count }: { rating: number | null; count: number }) {
  if (rating === null || count === 0) {
    return (
      <span className="stars stars-empty" title="No reviews yet">
        {[0, 1, 2, 3, 4].map((i) => (
          <Star key={i} filled={false} />
        ))}
        <span className="stars-label">No reviews yet</span>
      </span>
    )
  }
  const full = Math.round(rating)
  return (
    <span className="stars" title={`${rating.toFixed(1)} out of 5`}>
      {[0, 1, 2, 3, 4].map((i) => (
        <Star key={i} filled={i < full} />
      ))}
      <span className="stars-label">
        {rating.toFixed(1)} ({count})
      </span>
    </span>
  )
}
