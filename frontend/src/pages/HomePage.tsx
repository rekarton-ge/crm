import React from 'react'
import { Typography } from 'antd'

const HomePage: React.FC = () => {
  return (
    <div className="p-6">
      <Typography.Title>CRM Система</Typography.Title>
      <Typography.Paragraph>
        Добро пожаловать в вашу CRM систему
      </Typography.Paragraph>
    </div>
  )
}

export default HomePage