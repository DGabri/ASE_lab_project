import axios from 'axios'

const logout = async (access_token, user_id) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.post(
        `https://localhost:3000/auth/logout/${user_id}`,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )
    
    if (response.status != 200) {
        throw new Error(response.data.err)  
    }
    
    return response.data.msg
}

export default logout