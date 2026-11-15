import { Link } from 'react-router'
import { PageContainer } from '../../components/layout/PageContainer'
import { buttonStyles } from '../../components/ui'
import { paths } from '../router/paths'

export function NotFoundPage() {
  return (
    <PageContainer title="Page not found" description="The page you requested does not exist.">
      <Link to={paths.overview} className={buttonStyles({ variant: 'secondary' })}>
        Return to overview
      </Link>
    </PageContainer>
  )
}
