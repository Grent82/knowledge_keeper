import { SubmitButton } from "./SubmitButton";
import { buildCategoryLabel } from "./categoryUtils";
import type {
  Category,
  CategoryVisibilityAssignment,
  MediaItem,
  MediaItemVisibilityAssignment,
  RestrictedUser,
} from "./types";

type RestrictedUserAccessCardProps = {
  restrictedUsers: RestrictedUser[];
  selectedRestrictedUserId: number | null;
  categories: Category[];
  mediaItems: MediaItem[];
  categoryAssignments: CategoryVisibilityAssignment[];
  mediaAssignments: MediaItemVisibilityAssignment[];
  userError: string;
  visibilityError: string;
  onSelectRestrictedUser: (userId: number | null) => void;
  onCreateRestrictedUser: (username: string, password: string, email: string) => Promise<void>;
  onSaveVisibility: (
    userId: number,
    categoryIds: number[],
    mediaItemIds: number[],
  ) => Promise<void>;
};

export function RestrictedUserAccessCard({
  restrictedUsers,
  selectedRestrictedUserId,
  categories,
  mediaItems,
  categoryAssignments,
  mediaAssignments,
  userError,
  visibilityError,
  onSelectRestrictedUser,
  onCreateRestrictedUser,
  onSaveVisibility,
}: RestrictedUserAccessCardProps) {
  const selectedUser = restrictedUsers.find((user) => user.id === selectedRestrictedUserId) ?? null;
  const selectedCategoryIds = new Set(
    categoryAssignments
      .filter((assignment) => assignment.user === selectedRestrictedUserId)
      .map((assignment) => assignment.category),
  );
  const selectedMediaIds = new Set(
    mediaAssignments
      .filter((assignment) => assignment.user === selectedRestrictedUserId)
      .map((assignment) => assignment.media_item),
  );
  const sortedCategories = [...categories].sort((left, right) =>
    buildCategoryLabel(categories, left).localeCompare(buildCategoryLabel(categories, right)),
  );
  const sortedMediaItems = [...mediaItems].sort((left, right) => left.title.localeCompare(right.title));

  return (
    <article className="card">
      <h2>Restricted Access</h2>
      <p className="muted">Create a limited second user and assign visible categories or media.</p>

      <form
        className="stack-form"
        action={async (formData) => {
          const username = String(formData.get("username") ?? "").trim();
          const password = String(formData.get("password") ?? "");
          const email = String(formData.get("email") ?? "").trim();

          if (!username || !password) {
            return;
          }

          await onCreateRestrictedUser(username, password, email);
        }}
      >
        <label className="field">
          <span>Username</span>
          <input name="username" required type="text" />
        </label>
        <label className="field">
          <span>Password</span>
          <input name="password" required type="password" />
        </label>
        <label className="field">
          <span>Email</span>
          <input name="email" type="email" />
        </label>
        {userError ? <p className="error-text">{userError}</p> : null}
        <SubmitButton pendingLabel="Creating...">Create restricted user</SubmitButton>
      </form>

      <div className="field">
        <span>Selected restricted user</span>
        {restrictedUsers.length === 0 ? (
          <p className="empty-state">No restricted users yet.</p>
        ) : (
          <select
            onChange={(event) => {
              const nextValue = event.target.value;
              onSelectRestrictedUser(nextValue ? Number(nextValue) : null);
            }}
            value={selectedRestrictedUserId ?? ""}
          >
            <option value="">Choose a user</option>
            {restrictedUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {user.username}
              </option>
            ))}
          </select>
        )}
      </div>

      {selectedUser ? (
        <form
          className="stack-form"
          action={async (formData) => {
            const categoryIds = formData
              .getAll("categories")
              .map((value) => Number(value))
              .filter((value) => !Number.isNaN(value));
            const mediaItemIds = formData
              .getAll("mediaItems")
              .map((value) => Number(value))
              .filter((value) => !Number.isNaN(value));

            await onSaveVisibility(selectedUser.id, categoryIds, mediaItemIds);
          }}
        >
          <div className="field">
            <span>Visible categories for {selectedUser.username}</span>
            {sortedCategories.length === 0 ? (
              <p className="empty-state">No categories available.</p>
            ) : (
              <div className="checkbox-grid">
                {sortedCategories.map((category) => (
                  <label key={category.id} className="checkbox-option">
                    <input
                      defaultChecked={selectedCategoryIds.has(category.id)}
                      name="categories"
                      type="checkbox"
                      value={category.id}
                    />
                    <span>{buildCategoryLabel(categories, category)}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="field">
            <span>Directly visible media items</span>
            {sortedMediaItems.length === 0 ? (
              <p className="empty-state">No media items available.</p>
            ) : (
              <div className="checkbox-grid">
                {sortedMediaItems.map((item) => (
                  <label key={item.id} className="checkbox-option">
                    <input
                      defaultChecked={selectedMediaIds.has(item.id)}
                      name="mediaItems"
                      type="checkbox"
                      value={item.id}
                    />
                    <span>{item.title}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {visibilityError ? <p className="error-text">{visibilityError}</p> : null}
          <SubmitButton>Save visibility</SubmitButton>
        </form>
      ) : null}
    </article>
  );
}
