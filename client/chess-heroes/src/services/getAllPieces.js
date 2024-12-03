import axios from 'axios'

const getAllPieces = async (access_token) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.get(
        "https://localhost:3000/piece/piece/all",
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

    return response.data.pieces
}

export default getAllPieces